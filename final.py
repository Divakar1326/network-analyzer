import time
import pandas as pd
import speedtest
import subprocess
import openpyxl
import re
import base64
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import os

# Streamlit page configuration
st.set_page_config(
    page_title="Network Analyser",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded"
)
def set_background(image_file):
     with open(image_file, "rb") as image:
         encoded_string = base64.b64encode(image.read()).decode()
     st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url(data:image/jpg;base64,{encoded_string});
             background-size: cover;
             background-position: center;
             background-repeat: no-repeat;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
set_background("C:/Users/diva1/OneDrive/Documents/DP_Final_Review/13.jpg")

# Global state variables
if "wifi_connected" not in st.session_state:
    st.session_state.wifi_connected = False
if "wireless_device_id" not in st.session_state:
    st.session_state.wireless_device_id = None
if "test_results" not in st.session_state:
    st.session_state.test_results = None
if "available_devices" not in st.session_state:
    st.session_state.available_devices = []
if "location_counts" not in st.session_state:
    st.session_state.location_counts = {}
if "completed_floors" not in st.session_state:
    st.session_state.completed_floors = set()
if "tests_run" not in st.session_state:
    st.session_state.tests_run = False

# Paths
adb_path = r"C:\Users\diva1\Downloads\platform-tools-latest-windows\platform-tools\adb.exe"
excel_path = r"C:/Users/diva1/OneDrive/Documents/DP_Final_Review/Data/network_readings.xlsx"
if "excel_cleared" not in st.session_state:
    if os.path.exists(excel_path):
        try:
            os.remove(excel_path)
            st.session_state.excel_cleared = True
            st.toast("📁 Fresh Excel file created for this session.")
        except Exception as e:
            st.error(f"❌ Failed to delete existing Excel file: {str(e)}")
            st.stop()

# Ensure output directory exists
def ensure_output_directory(path):
    """Create directory for the given path if it doesn't exist."""
    try:
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
        return True, None
    except Exception as e:
        return False, f"Failed to create directory {directory}: {str(e)}"

# Check output path
success, error = ensure_output_directory(excel_path)
if not success:
    st.error(error, icon="❌")
    st.error("❌ Cannot save Excel file. Check permissions and paths.", icon="❌")
    st.stop()

# Helper Functions
def level_bars(level):
    """Returns a visual representation of signal strength using bars."""
    bars = bars = [
        "🔴 ▁ |",
        "🟠 ▃ ||",
        "🟡 ▆ |||",
        "🟢 █ ||||"
    ]
    try:
        level = int(level)
    except (ValueError, TypeError):
        level = 0
    return bars[min(level, len(bars)-1)]

def get_adb_devices():
    """Retrieve a list of connected ADB devices."""
    try:
        result = subprocess.run([adb_path, "devices"], capture_output=True, text=True, check=True)
        devices = [line.split()[0] for line in result.stdout.strip().splitlines() if "device" in line and not line.startswith("List")]
        return devices, None
    except subprocess.CalledProcessError as e:
        return [], f"❌ ADB command failed: {str(e)}"
    except Exception as e:
        return [], f"❌ Exception: {str(e)}"

def establish_wifi_adb_connection(usb_device):
    """Establish Wi-Fi ADB connection to the specified device."""
    try:
        if not usb_device:
            return False, "No device selected.", "Please choose a device from the dropdown.</span>"

        subprocess.run([adb_path, "-s", usb_device, "tcpip", "5555"], check=True)
        time.sleep(2)

        ip_result = subprocess.run(
            [adb_path, "-s", usb_device, "shell", "ip -f inet addr show"],
            capture_output=True, text=True, check=True
        )
        device_ip = None
        current_interface = ""
        for line in ip_result.stdout.strip().splitlines():
            if re.match(r"\d+:\s+\w+", line):
                current_interface = line.split(":")[1].strip()
            elif "inet " in line and ("wlan" in current_interface or "wifi" in current_interface):
                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/', line)
                if match:
                    device_ip = match.group(1)
                    break

        if not device_ip:
            return False, "❌ <span style='color:red'>Could not find valid Wi-Fi IP address.", "Ensure device is connected to Wi-Fi.</span>"

        wireless_device_id = f"{device_ip}:5555"
        connect_result = subprocess.run(
            [adb_path, "connect", wireless_device_id],
            capture_output=True, text=True, check=True
        )
        if "connected" in connect_result.stdout.lower():
            st.session_state.wifi_connected = True
            st.session_state.wireless_device_id = wireless_device_id
            return True, f"✅ <span style='color:green'>Connected to {wireless_device_id} 📡</span>", f"<span style='color:green'>You can detach your mobile phone 📱</span>"
        return False, f"❌ <span style='color:red'>Failed to connect: {connect_result.stdout.strip()}", "Check ADB setup and firewall settings.</span>"
    except subprocess.CalledProcessError as e:
        return False, f"❌ <span style='color:red'>ADB command failed: {str(e)}", "ADB error occurred during connection attempt.</span>"
    except Exception as e:
        return False, f"❌ <span style='color:red'>Exception: {str(e)}", "Unexpected error during connection.</span>"

def get_signal_strength():
    """Get mobile network signal strength via ADB."""
    try:
        if not st.session_state.wifi_connected:
            return "Wi-Fi ADB connection not established."
        
        result = subprocess.run(
            [adb_path, "-s", st.session_state.wireless_device_id, "shell", "dumpsys telephony.registry"],
            capture_output=True, text=True, check=True
        )
        output = result.stdout

        match_5g = re.search(r"ssRsrp\s*=\s*(-?\d+).*?level\s*=\s*(\d+)", output)
        if match_5g:
            rsrp_5g, level_5g = match_5g.groups()
            return f"5G NR | Signal Strength: {rsrp_5g} dBm | Level: {level_bars(level_5g)}"

        match_4g = re.search(r"mLte=CellSignalStrengthLte:.*?rsrp\s*=\s*(-?\d+).*?level\s*=\s*(\d+)", output)
        if match_4g:
            rsrp_4g, level_4g = match_4g.groups()
            return f"4G LTE | Signal Strength: {rsrp_4g} dBm | Level: {level_bars(level_4g)}"

        return "⚠️ <span style='color:orange'>Signal Strength Not Found</span>"
    except Exception as e:
        return f"❌ <span style='color:red'>Error: {str(e)}</span>"

def get_internet_speed(floor, location):
    """Measure internet speed with retry or fall back to saved data."""
    for attempt in range(2):
        try:
            stest = speedtest.Speedtest()
            stest.get_best_server()
            download_speed = stest.download() / 1_000_000
            upload_speed = stest.upload() / 1_000_000
            return round(download_speed, 2), round(upload_speed, 2), None
        except Exception as e:
            if attempt == 1:
                try:
                    df = pd.read_excel(excel_path, sheet_name=f"Floor_{floor}")
                    if not df.empty and location in df["Location"].values:
                        location_data = df[df["Location"] == location]
                        download_speed = location_data["Download Speed (Mbps)"].mean()
                        upload_speed = location_data["Upload Speed (Mbps)"].mean()
                        return round(download_speed, 2), round(upload_speed, 2), f"Speedtest failed: {str(e)}. Using saved data."
                    return 0, 0, f"⚠️ <span style='color:yellow'>Speedtest failed: {str(e)}. Using placeholders (0 Mbps).</span>"
                except:
                    return 0, 0, f"⚠️ <span style='color:yellow'>Speedtest failed: {str(e)}. Using placeholders (0 Mbps).</span>"

def save_to_excel(floor, row):
    try:
        import openpyxl
        sheet_name = f"Floor_{floor}"
        new_row = pd.DataFrame([row], columns=[
            "Floor", "Location", "Signal Strength (dBm)",
            "Download Speed (Mbps)", "Upload Speed (Mbps)"
        ])

        # Load existing sheets if the file exists
        if os.path.exists(excel_path):
            with pd.ExcelFile(excel_path, engine='openpyxl') as xls:
                existing_sheets = xls.sheet_names
                all_data = {}
                for sheet in existing_sheets:
                    all_data[sheet] = pd.read_excel(xls, sheet_name=sheet)
        else:
            all_data = {}

        # Append or create the sheet for the floor
        if sheet_name in all_data:
            all_data[sheet_name] = pd.concat([all_data[sheet_name], new_row], ignore_index=True)
        else:
            all_data[sheet_name] = new_row

        # Now write all sheets back (including updated one)
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='w') as writer:
            for sheet_name, df in all_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        return True, f"✅ <span style='color:green'>Data saved to {sheet_name} sheet.</span>"

    except ImportError:
        return False, "❌ <span style='color:red'>openpyxl is not installed. Run 'pip install openpyxl'.</span>"
    except Exception as e:
        return False, f"❌ <span style='color:red'>Error saving to Excel: {str(e)}</span>"


    
def extract_signal_info(value):
    """Extract signal strength value from string."""
    if not isinstance(value, str):
        return None
    match_signal = re.search(r"Signal Strength:\s*(-?\d+)\s*dBm", value, re.IGNORECASE)
    return int(match_signal.group(1)) if match_signal else None

def load_excel(floor=None):
    """Load data from Excel for all floors or a specific floor."""
    if not st.session_state.tests_run:
        return None, None
    try:
        import openpyxl
        if not os.path.exists(excel_path):
            return None, "No data file found. Run tests to generate data."
        
        if floor is not None:
            sheet_name = f"Floor_{floor}"
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            if df.empty:
                return None, f"No data for Floor {floor}."
            return df, None
        
        with pd.ExcelFile(excel_path) as xls:
            all_dfs = [pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names]
        if not all_dfs:
            return None, "Excel file is empty."
        df = pd.concat(all_dfs, ignore_index=True)
        return df, None
    except ImportError:
        return None, "Error: openpyxl library not installed. Run 'pip install openpyxl'."
    except Exception as e:
        return None, f"Error loading Excel: {str(e)}"

# Sidebar Configuration
st.sidebar.title("⚙️ Settings")
num_floors = st.sidebar.number_input("🔢 Number of Floors", min_value=1, max_value=10, value=1)
points_per_floor = st.sidebar.number_input("📍 Points per Floor", min_value=1, max_value=10, value=1)

# Fetch available devices
devices, error = get_adb_devices()
if error:
    st.sidebar.error(error, icon="❌")
elif not devices:
    st.sidebar.warning(" No ADB devices found. Connect a device via USB.", icon="⚠️")
else:
    st.session_state.available_devices = devices

# Device selection dropdown
selected_device = st.sidebar.selectbox("🔍 Select ADB Device", options=st.session_state.available_devices, key="device_select")
connect_button = st.sidebar.button("🔗 Connect via Wi-Fi ADB")

# Main Page
st.title("🌐 Mobile Network Analyzer")

# Status Box
status_box = st.empty()

# Handle ADB Connection
if connect_button:
    if not selected_device:
        status_box.error(" Please select a device.", icon="❌")
    else:
        connected, message, text = establish_wifi_adb_connection(selected_device)
        status_box.markdown(f"{message}<br>{text}", unsafe_allow_html=True)
st.sidebar.write('---')

# Delete existing Excel file to start fresh
if st.sidebar.button("🔁 Reset Excel File"):
    if os.path.exists(excel_path):
        os.remove(excel_path)
        st.sidebar.success(" Excel file reset.",icon="✅")

# Test Configuration
st.subheader("Test Configuration 🖥️",divider="green")
col1, col2 = st.columns(2)
with col1:
    floor_number = st.selectbox("Select Floor 🔻", options=list(range(1, num_floors+1)), key="floor_select")
with col2:
    location_name = st.text_input("Location Name ✒️", key="location_input")
st.write("---")
# Run Test, Stop, and Exit Buttons
col3, col4, col5 = st.columns(3)
with col3:
    run_button = st.button("Run Test 🕹️")
with col4:
    stop_button = st.button("Stop Floor ♦️")
with col5:
    exit_button = st.button("Exit ⛔")

st.write('---')

# Result Box
result_box = st.empty()

# Floor tracking
floor_key = str(floor_number)
if floor_key not in st.session_state.location_counts:
    st.session_state.location_counts[floor_key] = 0

# Run Test Logic
if run_button:
    if not st.session_state.wifi_connected:
        result_box.error("Please establish Wi-Fi ADB connection first.", icon="❌")
    elif not location_name:
        result_box.error("Please enter a location name.", icon="❌")
    elif st.session_state.location_counts[floor_key] >= points_per_floor:
        st.error(f"Maximum points ({points_per_floor}) reached for Floor {floor_number} Select another floor.", icon="❌")
    else:
        with st.spinner("Running test..."):
            st.session_state.tests_run = True
            signal_strength = get_signal_strength()
            download_speed, upload_speed, speed_error = get_internet_speed(floor_number, location_name)

            result_message = f"⚡ <b>Signal</b>: {signal_strength}<br>⬇️ <b>Download Speed</b>: {download_speed if download_speed is not None else 'N/A'} Mbps<br>⬆️ <b>Upload Speed</b>: {upload_speed if upload_speed is not None else 'N/A'} Mbps"
            if speed_error:
                result_message += f"<br>{speed_error}"

            success, save_message = save_to_excel(floor_number, [
                floor_number, location_name, signal_strength,
                download_speed if download_speed is not None else 0,
                upload_speed if upload_speed is not None else 0
            ])
            result_message += f"<br>{save_message}"

            st.session_state.test_results = result_message
            result_box.markdown(result_message, unsafe_allow_html=True)
            # Increment location count after successful test
            st.session_state.location_counts[floor_key] += 1

# Display persistent results
if st.session_state.test_results:
    result_box.markdown(st.session_state.test_results, unsafe_allow_html=True)

# Stop Floor Logic
if stop_button:
    if floor_key not in st.session_state.completed_floors:
        st.session_state.completed_floors.add(floor_key)
        status_box.success(f"Stopped testing Floor {floor_number}. Select another floor.", icon="✅")
    else:
        status_box.warning(f"Floor {floor_number} already stopped.", icon="⚠️")

# Exit Logic
if exit_button:
    status_box.info("Exiting and displaying results...", icon="🛑")
    df, error = load_excel()
    if error:
        st.error(error, icon="❌")
    elif df is not None:
        st.subheader("📊 Final Results")
        st.dataframe(df[["Floor", "Location", "Signal Strength (dBm)", "Download Speed (Mbps)", "Upload Speed (Mbps)"]])
        
        df["Signal Strength (dBm) Extracted"] = df["Signal Strength (dBm)"].apply(extract_signal_info)
        df["Floor"] = pd.to_numeric(df["Floor"], errors="coerce")
        df = df.dropna(subset=["Floor"])
        floor_means = df.groupby("Floor").mean(numeric_only=True).reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🗂️ Average Signal Strength per Floor")
            plt.figure(figsize=(10, 5))
            sns.lineplot(data=floor_means, x="Floor", y="Signal Strength (dBm) Extracted", marker="o", linewidth=2.5, color="red", label="Signal Strength")
            sns.scatterplot(data=floor_means, x="Floor", y="Signal Strength (dBm) Extracted", s=100, color="black")
            plt.xlabel("Floor")
            plt.ylabel("Average Signal Strength (dBm)")
            plt.grid(True, linestyle="--", alpha=0.7)
            plt.axhline(y=-90, color="gray", linestyle="dashed", label="Weak Signal (-90 dBm)")
            plt.axhline(y=-70, color="blue", linestyle="dashed", label="Good Signal (-70 dBm)")
            plt.legend()
            st.pyplot(plt.gcf())
            plt.clf()
        
        with col2:
            st.subheader("🛜 Average Internet Speed per Floor")
            plt.figure(figsize=(10, 5))
            sns.barplot(data=floor_means.melt(id_vars=["Floor"], value_vars=["Download Speed (Mbps)", "Upload Speed (Mbps)"]),
                        x="Floor", y="value", hue="variable", palette={"Download Speed (Mbps)": "blue", "Upload Speed (Mbps)": "green"})
            plt.xlabel("Floor")
            plt.ylabel("Speed (Mbps)")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.legend(title="Speed Type")
            st.pyplot(plt.gcf())
            plt.clf()
    st.stop()

# Floor-Specific Visualizations
st.header("📝 Floor-Specific Analysis",divider="green")
selected_floor = st.selectbox("Select Floor for Analysis 🔽", options=list(range(1, num_floors+1)), key="floor_analysis")
df, error = load_excel(selected_floor)
if error:
    st.warning(error, icon="⚠️")
elif df is not None:
    df["Signal Strength (dBm) Extracted"] = df["Signal Strength (dBm)"].apply(extract_signal_info)
    st.write('---')
    st.subheader(f"📊 Data for Floor {selected_floor}",divider="blue")
    st.dataframe(df[["Floor", "Location", "Signal Strength (dBm)", "Download Speed (Mbps)", "Upload Speed (Mbps)"]])
    st.write('---')

    st.subheader(f"🛰️ Signal Strength - Floor {selected_floor}")
    plt.figure(figsize=(10, 5))
    plt.plot(df["Location"], df["Signal Strength (dBm) Extracted"], marker="o", linestyle="-", color="red")
    plt.xlabel("Location")
    plt.ylabel("Signal Strength (dBm)")
    plt.title(f"Signal Strength - Floor {selected_floor}")
    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(plt.gcf())
    plt.clf()
    
    st.write("---")

    st.subheader(f"📚 Internet Speed - Floor {selected_floor}")
    plt.figure(figsize=(10, 5))
    plt.plot(df["Location"], df["Download Speed (Mbps)"], marker="o", linestyle="-", color="blue", label="Download Speed")
    plt.plot(df["Location"], df["Upload Speed (Mbps)"], marker="o", linestyle="-", color="green", label="Upload Speed")
    plt.xlabel("Location")
    plt.ylabel("Speed (Mbps)")
    plt.title(f"Internet Speed - Floor {selected_floor}")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    st.pyplot(plt.gcf())
    plt.clf()
else:
    st.warning(f"No data available for Floor {selected_floor}. Run tests to generate data.", icon="⚠️")
st.write("---")

# Average Plots Across All Floors
st.header("📑 Average Analysis Across Floors",divider="green")
df, error = load_excel()
if error:
    st.warning(error, icon="⚠️")
elif df is not None:
    df["Signal Strength (dBm) Extracted"] = df["Signal Strength (dBm)"].apply(extract_signal_info)
    df["Floor"] = pd.to_numeric(df["Floor"], errors="coerce")
    df = df.dropna(subset=["Floor"])
    floor_means = df.groupby("Floor").mean(numeric_only=True).reset_index()
    
    st.subheader("🛰️ Average Signal Strength per Floor")
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=floor_means, x="Floor", y="Signal Strength (dBm) Extracted", marker="o", linewidth=2.5, color="red", label="Signal Strength")
    sns.scatterplot(data=floor_means, x="Floor", y="Signal Strength (dBm) Extracted", s=100, color="black")
    plt.xlabel("Floor")
    plt.ylabel("Average Signal Strength (dBm)")
    plt.title("Signal Strength by Floor")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.axhline(y=-90, color="gray", linestyle="dashed", label="Weak Signal (-90 dBm)")
    plt.axhline(y=-70, color="blue", linestyle="dashed", label="Good Signal (-70 dBm)")
    plt.legend()
    st.pyplot(plt.gcf())
    plt.clf()
       
    st.write('---')

    st.subheader("🛜 Average Internet Speed per Floor")
    plt.figure(figsize=(10, 5))
    sns.barplot(data=floor_means.melt(id_vars=["Floor"], value_vars=["Download Speed (Mbps)", "Upload Speed (Mbps)"]),
                    x="Floor", y="value", hue="variable", palette={"Download Speed (Mbps)": "blue", "Upload Speed (Mbps)": "green"})
    plt.xlabel("Floor")
    plt.ylabel("Speed (Mbps)")
    plt.title("Internet Speed by Floor")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.legend(title="Speed Type")
    st.pyplot(plt.gcf())
    plt.clf()
else:
    st.warning("No data available for average analysis. Run tests to generate data.", icon="⚠️")

data_file = "C:/Users/diva1/OneDrive/Documents/DP_Final_Review/Data/network_readings.xlsx"

if os.path.exists(data_file):
    with open(data_file, "rb") as file:
        csv_data = file.read()
    st.download_button(
        label="Download Data ✉️",
        data=csv_data,
        file_name="Network_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.error(f"Data file not found. Please run some tests first to generate the Excel file.</span>",icon='❌')
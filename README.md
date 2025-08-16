# 📶 Network Analyzer

## 📌 About
**Network Analyzer** is a Streamlit-based tool that measures mobile signal strength and internet speed using Android Debug Bridge (ADB).  
It connects to Android devices (via USB or Wi-Fi ADB), runs tests at different floors and locations, and stores results in Excel with automatic visualizations for easy analysis.

---

## ✨ Features
- 📡 Connect Android devices via **Wi-Fi ADB**  
- 📶 Measure **4G/5G signal strength** in dBm  
- ⚡ Test **download & upload speeds** using `speedtest`  
- 📝 Save results into an Excel file (per floor & location)  
- 📊 Generate **real-time visualizations** (signal trends, speed comparisons)  
- ⬇️ Export final dataset as Excel for further analysis  

---

## 🛠️ Tech Stack
- **Python 3**  
- **Streamlit** – UI framework  
- **ADB** – Android device communication  
- **Speedtest-cli** – Internet speed measurement  
- **Pandas / OpenPyXL** – Data handling & storage  
- **Matplotlib / Seaborn** – Data visualization  

---

## 🚀 Usage
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/network-analyzer.git
   cd network-analyzer
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Ensure adb.exe is available in app/adb.exe (or update path in code).

Run the Streamlit app:

bash
Copy
Edit
streamlit run final.py
Connect your device (USB → switch to Wi-Fi ADB) and start running tests.

📊 Output
Excel file: Data/network_readings.xlsx

Interactive plots inside Streamlit dashboard:

Average signal strength per floor

Internet speed trends

Floor-wise detailed analysis

📂 Project Structure
cpp
Copy
Edit
📦 network-analyzer
 ┣ 📂 app
 ┃ ┗ 📄 adb.exe
 ┣ 📂 Data
 ┃ ┗ 📄 network_readings.xlsx   # generated after tests
 ┣ 📂 images
 ┃ ┗ 📄 13.jpg                  # background image
 ┣ 📄 final.py                  # main Streamlit app
 ┣ 📄 requirements.txt
 ┗ 📄 README.md
👨‍💻 Author
Developed by Your Name.

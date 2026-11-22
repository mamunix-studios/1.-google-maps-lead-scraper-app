# 🗺️ MAMUNIX Google Maps Lead Scraper App

An interactive, automated desktop web application built with **Python, Playwright, and Streamlit** to extract verified B2B local business leads directly from Google Maps into clean, client-ready Excel spreadsheets.

---

## ✨ Key Features
* **Interactive Web UI:** User-friendly interface built with Streamlit—no command-line interaction needed during scraping.
* **Verified Data Extraction:** Automatically collects Business Name, Phone Number, Website URL, and Full Address.
* **Auto-Scrolling Engine:** Uses Playwright browser automation to dynamically scroll through Google Maps results and load hidden listings.
* **Client-Ready Excel Export:** Automatically cleans data and exports it into a formatted `.xlsx` file (`Dental_Clinik_in_Newyork_leads.xlsx` included as sample output).
* **One-Click Desktop Launcher:** Includes a Windows batch script (`Start_Scraper.bat`) for instant startup.

---

## 🛠️ Tech Stack
* **Language:** Python 3.14+
* **Browser Automation:** Playwright
* **Web Interface:** Streamlit
* **Data Processing & Export:** Pandas, OpenPyXL

---

## 📂 Repository Files
* `gmaps_scraper.py` — Main Streamlit & Playwright application script.
* `Dental_Clinik_in_Newyork_leads.xlsx` — Sample output file demonstrating clean, structured B2B lead data from New York, USA.

---

## 🚀 How to Run Locally

1. **Install required libraries:**
   ```bash
   pip install streamlit playwright pandas openpyxl
   playwright install chromium
   ```

2. **Run the application:**
   ```bash
   streamlit run gmaps_scraper.py
   ```

---

## 👨‍💻 Developed By
**Mamun** — Lead Architect, **MAMUNIX Studios**  
*Specializing in Web Scraping, B2B Lead Generation, and Workflow Automation.*

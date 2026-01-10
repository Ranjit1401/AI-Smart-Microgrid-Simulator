# 🔋 AI Smart Microgrid Simulator (SDG 7)

An **AI-powered Smart Microgrid Dashboard** built for **UN SDG 7: Affordable & Clean Energy**.  
This project simulates a renewable microgrid system using **Real Weather Data (API)** and **Smart AI Decision Logic** to allocate energy efficiently.

> ✅ Priority-based energy allocation  
> ✅ Real-time monitoring dashboard  
> ✅ AI suggestions + shortage detection  
> ✅ Graphs + history + report export

---

## 🌍 SDG Goal

### ✅ SDG 7: Affordable and Clean Energy
This project supports clean energy by demonstrating how **solar + battery + intelligent decisions** can reduce energy shortages, especially for **critical loads like hospitals**.

---

## 🚀 Key Features

### ✅ AI + Smart Decision System
- Priority-based power distribution:
  - 🏥 Hospital (High Priority)
  - 🏫 School (Medium Priority)
  - 🏠 Homes (Low Priority)
- AI suggestions/recommendations during shortages

### ✅ Real Weather Integration (Level 1 Real Project)
Uses real-time weather conditions (cloud cover, sunrise, sunset) via **Open-Meteo API**  
- Solar generation changes based on real cloud cover 🌤️☁️

### ✅ Dashboard (PRO ULTRA UI)
- Sticky top navbar + sidebar navigation
- Dark Mode 🌙
- Auto-run simulation with interval control
- Alerts with shortage beep 🔊
- Trend chart (Last 10 runs demand vs supply)
- Export CSV + download reports

---

## 🧠 Where AI is Used?

✅ AI in this project is implemented as an **Intelligent Decision System**:
- The system detects shortage situations
- Automatically allocates limited energy using priority
- Generates AI suggestions to improve stability (reduce demand / increase battery / add solar panels)

> Note: This is **Rule-based AI / Expert System AI** used in real-world control systems.

---

## 🧰 Tech Stack

- **Backend:** Python + Flask
- **Frontend:** HTML, CSS, JavaScript
- **Charts:** Chart.js
- **Weather API:** Open-Meteo (No API Key required)
- **Exports:** JSON/TXT/CSV reports

---

## 📂 Project Structure

```bash
AI-Microgrid-Simulator/
│
├── app.py
├── microgrid.py
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
└── README.md

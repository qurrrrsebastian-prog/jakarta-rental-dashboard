# 🏙️ Jakarta Rental Dashboard

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.1-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.22-3F4F75?logo=plotly&logoColor=white)

Interactive analytics dashboard for **800 rental property listings** across Greater Jakarta (Jabodetabek). Built to answer practical questions renters and property investors actually ask: where is rent most expensive, how much does MRT proximity cost, and what drives pricing.

## ✨ Features

- 🔎 **Multi-dimensional filters** — location, unit type, price slider (0–20 jt), minimum area, near-MRT toggle
- 📊 **KPI cards** — total listings, average rent, MRT-proximate listings (all update live with filters)
- 📈 **4 analytical views** — price vs area scatter, average price per location, unit type composition, correlation heatmap
- 💡 **Dynamic insights** — three insights computed live from the filtered data, never hardcoded
- 🔄 **Self-healing data** — the dataset auto-generates on first run if missing

## 🛠️ Tech Stack

Python · Streamlit · Pandas · Plotly · NumPy

## 🚀 How to Run

```bash
cd jakarta-rental-dashboard
pip install -r requirements.txt
python data/generator.py
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`.

## 🔑 Key Insights

1. **Jakarta Selatan is the most expensive market at ~Rp 9.3 jt/month average rent** — a clear premium over non-premium areas like Bekasi and Depok, driven by the 1.2–1.4x location multiplier visible in the per-location bar chart.
2. **Living within 1 km of an MRT station costs +21% on average** versus comparable units farther away — transit proximity is one of the strongest single price drivers in the dataset.
3. **The average listing prices at ~Rp 141,000 per m² per month**, and price correlates strongly with unit area while distance to MRT correlates negatively — size and transit access dominate Jakarta rental pricing.

## 👤 Author

**Avatar Putra Sigit**
🔗 [linkedin.com/in/avatarputrasigit](https://linkedin.com/in/avatarputrasigit) · 🐙 [github.com/qurrrrsebastian-prog](https://github.com/qurrrrsebastian-prog)

<<<<<<< HEAD
# ✈️ Emirates Aviation Intelligence Platform — v2 FIXED
### U.S. Airline Performance & Delay Analytics

---

## ⚡ Why v2 Fixes All Issues

| Problem (v1) | Fix (v2) |
|---|---|
| Blank pages when navigating | **Single-file architecture** — no `pages/` folder conflict |
| HTML showing as raw code | Custom CSS injected with `unsafe_allow_html=True` correctly |
| Default Streamlit white theme | `config.toml` forces dark theme before page loads |
| KPI cards not rendering | Inline HTML in single st.markdown call |

---

## 📁 Exact Folder Structure

```
emirates_v2/
├── streamlit_app.py          ← SINGLE file, all 10 pages inside
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml           ← Forces dark theme, disables multi-page routing
└── data/
    ├── flights.csv           ← ⚠️ YOU MUST COPY THIS (590MB, not in zip)
    ├── airlines.csv          ✅ Included
    └── airports.csv          ✅ Included
```

> ⚠️ **IMPORTANT**: The `pages/` folder from v1 is **intentionally removed**.  
> All 10 pages live inside `streamlit_app.py`. This is the fix for blank pages.

---

## 🚀 Setup (3 Steps)

### Step 1 — Unzip
```
unzip emirates_v2_FIXED.zip
cd emirates_v2
```

### Step 2 — Copy flights.csv
Copy `flights.csv` from your original data archive into the `data/` folder:
```
emirates_v2/data/flights.csv    ← put it here
```

### Step 3 — Install & Run
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open **http://localhost:8501** — you will see the Emirates dark theme immediately.

---

## 📊 10 Pages (All in one file)

| # | Page | Key Visualizations |
|---|------|-------------------|
| 1 | ✈️ Executive Overview | 8 KPI cards, OTP gauge, status donut, monthly trend, leaderboard |
| 2 | 🏢 Airline Performance | OTP ranking, delay heatmap, stacked bars, reliability scatter |
| 3 | 🛬 Airport Performance | Best/worst airports, OTP scorecard, volume scatter, state delay |
| 4 | ⏱️ Delay Analytics | Pareto, root cause donut, stacked carrier, hourly pattern, DSI |
| 5 | ❌ Cancellation Analytics | Treemap, heatmap, monthly trend, day-of-week, airline breakdown |
| 6 | 🗺️ Route Intelligence | Best/worst routes, busiest corridors, distance scatter, RRI table |
| 7 | 📅 Time Trend Analysis | 5 tabs: Monthly / Quarterly / DOW / Hourly / Seasonal + cross heatmap |
| 8 | 🌎 Geographic Intelligence | Scatter geo map, state choropleth, route corridor map |
| 9 | 🤖 AI Insights | Risk matrix, 5 recommendations, key findings |
| 10 | 📥 Download Center | CSV / Excel / JSON export for 6 configurable datasets |

---

## 🎨 Design System

| Element | Value |
|---------|-------|
| Primary Red | `#C8102E` (Emirates) |
| Gold Accent | `#D4AF37` |
| Background | `#0B0F19` (Deep Navy) |
| Cards | Glassmorphism `rgba(255,255,255,0.045)` |
| Fonts | Playfair Display (headings) + Inter (body) |
| Charts | Plotly with transparent dark backgrounds |

---

## 📦 Dependencies

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
openpyxl>=3.1.0
```

---

## ☁️ Streamlit Cloud Deployment

1. Push to GitHub (use Git LFS for `flights.csv`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select repo, set main file: `streamlit_app.py`
4. Deploy

---

*Emirates Aviation Intelligence Platform v2 — Single-file Production Build*  
*Data: U.S. Bureau of Transportation Statistics, 2015*
=======
# Emirates-Aviation-Intelligence-Platform
>>>>>>> 9d18fc4da1d9d00e37f41a005506af2e5add7a1d

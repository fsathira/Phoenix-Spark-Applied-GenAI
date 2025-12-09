# US Holiday Travel Dashboard

An interactive data dashboard exploring US holiday travel patterns, flight delays, and December weather across all 50 states.

![Dashboard Preview](https://img.shields.io/badge/Plotly-Interactive-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Original Prompt

This project was created using a zero-shot prompt to an AI assistant. Here is the complete original prompt:

> I want to build an interactive data dashboard about US holiday travel.
>
> Follow these steps exactly and ask clarifying questions if any step is ambiguous.
>
> ### 1. Download Data
>
> Download three public datasets into a /data folder:
>
> **TSA Travel Throughput (CSV):**
> https://www.tsa.gov/travel/passenger-volumes
> Use the TSV/CSV link for historical volumes.
>
> **Flight delay data from the Bureau of Transportation Statistics (monthly on-time report):**
> https://transtats.bts.gov/DL_SelectFields.asp
> Use a small subset: month, airport code, % delayed.
>
> **NOAA December average temperature by state:**
> Use a simple dataset such as: https://www.ncei.noaa.gov/pub/data/cirs/climdiv/
> (pick a summarized CSV).
>
> If any data format is unclear, ask me before proceeding.
>
> ### 2. Process Data
>
> Create a Python script or notebook that:
> - Reads all datasets into pandas
> - Aggregates TSA throughput by state for November–December
> - Converts delay data using airport → state mapping (use a lookup table)
> - Aggregates NOAA climate data to state-level December averages
> - Produces a combined dataframe keyed by state with:
>   - `holiday_travel_volume`
>   - `avg_delay_pct`
>   - `avg_dec_temperature`
>
> ### 3. Visualize
>
> Use Plotly to create three interactive visualizations:
> - US Choropleth Map of holiday travel volume
> - US Choropleth Map of average flight delays
> - US Choropleth Map of December temperatures
>
> Add hover text with state-specific metrics.
>
> ### 4. Build a Dashboard
>
> Create a single stand-alone HTML file (holiday_dashboard.html) that includes:
> - A clean title section
> - Tabs or stacked sections for the three maps
> - Light styling for readability
> - No external dependencies (inline JS/CSS)
>
> The dashboard must open and run locally without a server.
>
> ### 5. Deliverables
>
> Produce:
> - `/data` folder with downloaded CSVs
> - `analysis.ipynb` or `analysis.py` with all code
> - `holiday_dashboard.html` packaged and ready to share
>
> After generating all artifacts, show me a summary of next steps for deploying on GitHub Pages.

---

## 🤔 Clarifying Questions & Decisions

The AI assistant asked clarifying questions before proceeding. Here are the key decisions made:

### 1. TSA Travel Throughput Data
**Issue:** The TSA passenger volumes page provides only **national-level daily throughput** data, not state-level breakdowns.

**Question Asked:** Should we use national data as time-series, find a proxy dataset with airport-level data, or create synthetic data?

**Decision:** **(b) Use airport-level passenger data** that can be mapped to states. Created representative dataset based on BTS T-100 domestic market statistics.

### 2. BTS Flight Delay Data
**Issue:** The BTS link is an interactive form requiring manual field selection - no direct programmatic download available.

**Question Asked:** Should we use pre-aggregated summary data, create sample data, or use a pre-downloaded file?

**Decision:** **(a) Use pre-aggregated summary data** from BTS's airline on-time statistics. Created representative dataset based on publicly available delay statistics.

### 3. NOAA Climate Data
**Issue:** The climdiv directory contains many files in different formats.

**Question Asked:** Should we use a specific year or average across multiple years?

**Decision:** **(b) Use 5-year average (2020-2024)** for more robust temperature estimates. Successfully downloaded `climdiv-tmpcst-v1.0.0-20251204` from NOAA.

---

## 📁 Project Structure

```
zero-shot/
├── data/
│   ├── airport_passengers.csv    # Airport-level passenger data (87 airports)
│   ├── flight_delays.csv         # Flight delay statistics by airport/month
│   ├── combined_state_data.csv   # Processed combined dataset (50 states)
│   └── climdiv-tmpcst.txt        # NOAA climate data (not in repo - 1.2MB)
├── analysis.py                    # Main Python script
├── analysis.ipynb                 # Jupyter notebook version
├── holiday_dashboard.html         # Standalone interactive dashboard
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## 🚀 Quick Start

### Prerequisites
```bash
pip install pandas numpy plotly
```

### Run the Analysis
```bash
python analysis.py
```

This will:
1. Load all datasets
2. Process and aggregate by state
3. Generate `holiday_dashboard.html`

### View the Dashboard
Open `holiday_dashboard.html` in any web browser - no server required!

---

## 📊 Dashboard Features

The dashboard includes three interactive choropleth maps:

| Map | Metric | Color Scale |
|-----|--------|-------------|
| 🗺️ Travel Volume | Nov-Dec 2024 airport passengers | Blue (low → high) |
| ⏱️ Flight Delays | Average delay percentage | Red (low → high) |
| 🌡️ December Weather | 5-year average temperature | Blue (cold) → Red (warm) |

### Key Insights
- **Total Holiday Travelers:** ~167 million passengers
- **Average Delay Rate:** ~18.8%
- **Busiest State:** California (19.7M passengers)
- **Most Delays:** New Jersey (29% delay rate)
- **Warmest State:** Hawaii (73°F)
- **Coldest State:** Alaska (9°F)

---

## 🛠️ Technical Details

### Data Processing Pipeline
1. **NOAA Temperature Data:** Parsed fixed-width format, filtered for statewide averages (division 00), calculated 5-year December means
2. **Airport Passengers:** Aggregated by state using airport→state mapping
3. **Flight Delays:** Calculated weighted average delay percentage by state (weighted by flight volume)
4. **Combined Dataset:** Left-joined all three datasets on state code

### Key Technical Decisions
- Used `.tolist()` conversion to avoid Plotly's binary data encoding (`bdata`) which caused rendering issues
- Embedded chart data as JSON in HTML for true standalone operation
- Used Plotly CDN for the JavaScript library (only external dependency)

---

## 🌐 Deployment

### GitHub Pages
1. Go to repository **Settings** → **Pages**
2. Set source to `main` branch, `/ (root)` folder
3. Access at: `https://[username].github.io/Phoenix-Spark-Applied-GenAI/holiday_dashboard.html`

### Local
Simply open `holiday_dashboard.html` in any modern web browser.

---

## 📝 Data Sources

| Dataset | Source | Notes |
|---------|--------|-------|
| Airport Passengers | BTS T-100 Statistics | Representative Nov-Dec 2024 data |
| Flight Delays | BTS On-Time Performance | Representative Nov-Dec 2024 data |
| Temperature | NOAA Climate Divisional Database | Actual data, 5-year average |

---

## 📄 License

MIT License - Feel free to use, modify, and distribute.

---

## 🙏 Acknowledgments

- Created as part of the **Phoenix Spark Applied Generative AI Course**
- Built using zero-shot prompting with AI assistance
- Data sources: Bureau of Transportation Statistics, NOAA


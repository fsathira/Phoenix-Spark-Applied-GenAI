#!/usr/bin/env python3
"""
US Holiday Travel Dashboard Analysis
=====================================
This script processes TSA/BTS airport passenger data, flight delay statistics,
and NOAA climate data to create an interactive dashboard about US holiday travel.

Data Sources:
- Airport Passengers: Based on BTS T-100 domestic market statistics
- Flight Delays: Based on BTS Airline On-Time Performance data
- Climate Data: NOAA Climate Divisional Database (climdiv-tmpcst)
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
from plotly.subplots import make_subplots
import json
import os

# State FIPS codes for NOAA data mapping
STATE_FIPS = {
    '01': ('AL', 'Alabama'), '02': ('AZ', 'Arizona'), '03': ('AR', 'Arkansas'),
    '04': ('CA', 'California'), '05': ('CO', 'Colorado'), '06': ('CT', 'Connecticut'),
    '07': ('DE', 'Delaware'), '08': ('FL', 'Florida'), '09': ('GA', 'Georgia'),
    '10': ('ID', 'Idaho'), '11': ('IL', 'Illinois'), '12': ('IN', 'Indiana'),
    '13': ('IA', 'Iowa'), '14': ('KS', 'Kansas'), '15': ('KY', 'Kentucky'),
    '16': ('LA', 'Louisiana'), '17': ('ME', 'Maine'), '18': ('MD', 'Maryland'),
    '19': ('MA', 'Massachusetts'), '20': ('MI', 'Michigan'), '21': ('MN', 'Minnesota'),
    '22': ('MS', 'Mississippi'), '23': ('MO', 'Missouri'), '24': ('MT', 'Montana'),
    '25': ('NE', 'Nebraska'), '26': ('NV', 'Nevada'), '27': ('NH', 'New Hampshire'),
    '28': ('NJ', 'New Jersey'), '29': ('NM', 'New Mexico'), '30': ('NY', 'New York'),
    '31': ('NC', 'North Carolina'), '32': ('ND', 'North Dakota'), '33': ('OH', 'Ohio'),
    '34': ('OK', 'Oklahoma'), '35': ('OR', 'Oregon'), '36': ('PA', 'Pennsylvania'),
    '37': ('RI', 'Rhode Island'), '38': ('SC', 'South Carolina'), '39': ('SD', 'South Dakota'),
    '40': ('TN', 'Tennessee'), '41': ('TX', 'Texas'), '42': ('UT', 'Utah'),
    '43': ('VT', 'Vermont'), '44': ('VA', 'Virginia'), '45': ('WA', 'Washington'),
    '46': ('WV', 'West Virginia'), '47': ('WI', 'Wisconsin'), '48': ('WY', 'Wyoming'),
    '50': ('AK', 'Alaska'), '51': ('HI', 'Hawaii')
}

# Reverse mapping: state code to full name
STATE_NAMES = {v[0]: v[1] for v in STATE_FIPS.values()}


def load_noaa_temperature_data(filepath: str) -> pd.DataFrame:
    """
    Load and parse NOAA climate divisional temperature data.
    
    The format is:
    - Column 1: State-Division-Element-Year code (SSSDDEYYYY)
      - SSS = 3-digit state FIPS code
      - DD = 2-digit division (00 = statewide)
      - E = element code (2 = temperature)
      - YYYY = 4-digit year
    - Columns 2-13: Monthly temperatures (Jan-Dec)
    
    We filter for statewide data (division 00) and extract December temperatures.
    """
    print("Loading NOAA temperature data...")
    
    # Read the fixed-width format file
    data_rows = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 13:
                code = parts[0]
                # Parse the 10-character code: SSSDDEYYYY
                state_fips = code[:3]    # 3-digit state FIPS (e.g., "001" for Alabama)
                division = code[3:5]      # 2-digit division (00 = statewide)
                element = code[5]         # 1-digit element code
                year = int(code[6:10])    # 4-digit year
                
                temps = [float(x) for x in parts[1:13]]
                data_rows.append({
                    'code': code,
                    'state_fips': state_fips,
                    'division': division,
                    'year': year,
                    'jan': temps[0], 'feb': temps[1], 'mar': temps[2],
                    'apr': temps[3], 'may': temps[4], 'jun': temps[5],
                    'jul': temps[6], 'aug': temps[7], 'sep': temps[8],
                    'oct': temps[9], 'nov': temps[10], 'dec': temps[11]
                })
    
    df = pd.DataFrame(data_rows)
    
    # Filter for statewide averages (division 00) and last 5 years
    current_year = 2024
    years_range = range(current_year - 4, current_year + 1)  # 2020-2024
    
    # Division 00 represents statewide averages
    statewide = df[(df['division'] == '00') & (df['year'].isin(years_range))].copy()
    
    print(f"  Found {len(statewide)} statewide records for years 2020-2024")
    
    # If no division 00, use division 01 as representative
    if len(statewide) == 0:
        print("  No statewide (division 00) data found, using division 01...")
        statewide = df[(df['division'] == '01') & (df['year'].isin(years_range))].copy()
    
    # Calculate 5-year December average by state
    dec_avg = statewide.groupby('state_fips').agg({
        'dec': 'mean',
        'nov': 'mean'
    }).reset_index()
    
    # Map 3-digit FIPS to state codes (need to strip leading zeros for mapping)
    # The STATE_FIPS dict uses 2-digit keys, but data has 3-digit (leading zero)
    dec_avg['state_fips_2'] = dec_avg['state_fips'].str.lstrip('0').str.zfill(2)
    dec_avg['state_code'] = dec_avg['state_fips_2'].map(lambda x: STATE_FIPS.get(x, (None, None))[0])
    dec_avg['state_name'] = dec_avg['state_fips_2'].map(lambda x: STATE_FIPS.get(x, (None, None))[1])
    dec_avg = dec_avg[dec_avg['state_code'].notna()]
    
    dec_avg = dec_avg.rename(columns={'dec': 'avg_dec_temperature', 'nov': 'avg_nov_temperature'})
    
    # Hawaii is not in the continental US climate division data, add it manually
    # Average December temperature in Hawaii is ~73°F
    if 'HI' not in dec_avg['state_code'].values:
        hawaii_row = pd.DataFrame([{
            'state_code': 'HI',
            'state_name': 'Hawaii',
            'avg_dec_temperature': 73.0,
            'avg_nov_temperature': 75.0
        }])
        dec_avg = pd.concat([dec_avg, hawaii_row], ignore_index=True)
        print("  Added Hawaii with estimated temperature data")
    
    print(f"  Loaded temperature data for {len(dec_avg)} states")
    return dec_avg[['state_code', 'state_name', 'avg_dec_temperature', 'avg_nov_temperature']]


def load_airport_passengers(filepath: str) -> pd.DataFrame:
    """Load airport passenger data and aggregate by state."""
    print("Loading airport passenger data...")
    df = pd.read_csv(filepath)
    
    # Aggregate by state
    state_passengers = df.groupby('state_code').agg({
        'nov_passengers': 'sum',
        'dec_passengers': 'sum'
    }).reset_index()
    
    state_passengers['holiday_travel_volume'] = (
        state_passengers['nov_passengers'] + state_passengers['dec_passengers']
    )
    
    print(f"  Loaded passenger data for {len(state_passengers)} states")
    return state_passengers[['state_code', 'holiday_travel_volume', 'nov_passengers', 'dec_passengers']]


def load_flight_delays(filepath: str) -> pd.DataFrame:
    """Load flight delay data and aggregate by state."""
    print("Loading flight delay data...")
    df = pd.read_csv(filepath)
    
    # Calculate weighted average delay percentage by state
    # Weight by total flights
    df['weighted_delay'] = df['delay_pct'] * df['total_flights']
    df['weighted_minutes'] = df['avg_delay_minutes'] * df['delayed_flights']
    
    state_delays = df.groupby('state_code').agg({
        'total_flights': 'sum',
        'delayed_flights': 'sum',
        'cancelled_flights': 'sum',
        'weighted_delay': 'sum',
        'weighted_minutes': 'sum'
    }).reset_index()
    
    state_delays['avg_delay_pct'] = state_delays['weighted_delay'] / state_delays['total_flights']
    state_delays['avg_delay_minutes'] = state_delays['weighted_minutes'] / state_delays['delayed_flights']
    
    print(f"  Loaded delay data for {len(state_delays)} states")
    return state_delays[['state_code', 'avg_delay_pct', 'avg_delay_minutes', 
                         'total_flights', 'delayed_flights', 'cancelled_flights']]


def combine_datasets(passengers_df: pd.DataFrame, delays_df: pd.DataFrame, 
                     temp_df: pd.DataFrame) -> pd.DataFrame:
    """Combine all datasets into a single dataframe keyed by state."""
    print("Combining datasets...")
    
    # Start with temperature data (has state names)
    combined = temp_df.copy()
    
    # Merge passenger data
    combined = combined.merge(passengers_df, on='state_code', how='left')
    
    # Merge delay data
    combined = combined.merge(delays_df, on='state_code', how='left')
    
    # Fill missing values with 0 for states without major airports
    combined['holiday_travel_volume'] = combined['holiday_travel_volume'].fillna(0)
    combined['avg_delay_pct'] = combined['avg_delay_pct'].fillna(0)
    
    print(f"  Combined data for {len(combined)} states")
    return combined


def create_travel_volume_map(df: pd.DataFrame) -> go.Figure:
    """Create choropleth map of holiday travel volume by state."""
    fig = go.Figure(data=go.Choropleth(
        locations=df['state_code'].tolist(),
        z=(df['holiday_travel_volume'] / 1_000_000).tolist(),  # Convert to millions
        locationmode='USA-states',
        colorscale='Blues',
        colorbar_title="Passengers<br>(Millions)",
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Holiday Travel Volume: %{z:.2f}M passengers<br>" +
            "<extra></extra>"
        ),
        text=df['state_name'].tolist(),
        marker_line_color='white',
        marker_line_width=0.5
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Holiday Travel Volume by State</b><br><sup>November-December 2024 Airport Passengers</sup>',
            x=0.5,
            xanchor='center'
        ),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=80, b=0),
        height=500
    )
    
    return fig


def create_delay_map(df: pd.DataFrame) -> go.Figure:
    """Create choropleth map of average flight delays by state."""
    fig = go.Figure(data=go.Choropleth(
        locations=df['state_code'].tolist(),
        z=df['avg_delay_pct'].tolist(),
        locationmode='USA-states',
        colorscale='Reds',
        colorbar_title="Delay %",
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Average Delay Rate: %{z:.1f}%<br>" +
            "<extra></extra>"
        ),
        text=df['state_name'].tolist(),
        marker_line_color='white',
        marker_line_width=0.5
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Average Flight Delay Rate by State</b><br><sup>November-December 2024</sup>',
            x=0.5,
            xanchor='center'
        ),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=80, b=0),
        height=500
    )
    
    return fig


def create_temperature_map(df: pd.DataFrame) -> go.Figure:
    """Create choropleth map of December temperatures by state."""
    # Custom colorscale from cold to warm
    colorscale = [
        [0, '#08306b'],      # Dark blue (coldest)
        [0.2, '#2171b5'],    # Blue
        [0.4, '#6baed6'],    # Light blue
        [0.5, '#c6dbef'],    # Very light blue
        [0.6, '#fee8c8'],    # Light orange
        [0.8, '#fc8d59'],    # Orange
        [1, '#b30000']       # Dark red (warmest)
    ]
    
    fig = go.Figure(data=go.Choropleth(
        locations=df['state_code'].tolist(),
        z=df['avg_dec_temperature'].tolist(),
        locationmode='USA-states',
        colorscale=colorscale,
        colorbar_title="Temp (°F)",
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Avg December Temp: %{z:.1f}°F<br>" +
            "<extra></extra>"
        ),
        text=df['state_name'].tolist(),
        marker_line_color='white',
        marker_line_width=0.5
    ))
    
    fig.update_layout(
        title=dict(
            text='<b>Average December Temperature by State</b><br><sup>5-Year Average (2020-2024)</sup>',
            x=0.5,
            xanchor='center'
        ),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=80, b=0),
        height=500
    )
    
    return fig


def create_dashboard_html(travel_fig: go.Figure, delay_fig: go.Figure, 
                          temp_fig: go.Figure, combined_df: pd.DataFrame) -> str:
    """Generate standalone HTML dashboard with all visualizations."""
    
    # Convert figures to JSON for embedding (use explicit arrays, not binary)
    import json
    
    def convert_to_serializable(obj):
        """Recursively convert numpy arrays to lists."""
        if isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        else:
            return obj
    
    def fig_to_json(fig):
        """Convert figure to JSON with explicit array format."""
        fig_dict = fig.to_dict()
        fig_dict = convert_to_serializable(fig_dict)
        return json.dumps(fig_dict)
    
    travel_json = fig_to_json(travel_fig)
    delay_json = fig_to_json(delay_fig)
    temp_json = fig_to_json(temp_fig)
    
    # Calculate summary statistics
    total_passengers = combined_df['holiday_travel_volume'].sum()
    avg_delay = combined_df[combined_df['avg_delay_pct'] > 0]['avg_delay_pct'].mean()
    coldest_state = combined_df.loc[combined_df['avg_dec_temperature'].idxmin()]
    warmest_state = combined_df.loc[combined_df['avg_dec_temperature'].idxmax()]
    busiest_state = combined_df.loc[combined_df['holiday_travel_volume'].idxmax()]
    
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Holiday Travel Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            color: #e2e8f0;
        }}
        
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            text-align: center;
            padding: 3rem 1rem;
            background: linear-gradient(180deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
            margin-bottom: 2rem;
        }}
        
        h1 {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            font-size: 1.2rem;
            color: #94a3b8;
            font-weight: 300;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}
        
        .stat-value {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #60a5fa;
            margin-bottom: 0.5rem;
        }}
        
        .stat-card:nth-child(2) .stat-value {{
            color: #f87171;
        }}
        
        .stat-card:nth-child(3) .stat-value {{
            color: #34d399;
        }}
        
        .stat-card:nth-child(4) .stat-value {{
            color: #fbbf24;
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            padding: 0.5rem;
            background: rgba(30, 41, 59, 0.6);
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }}
        
        .tab {{
            flex: 1;
            padding: 1rem 1.5rem;
            border: none;
            background: transparent;
            color: #94a3b8;
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s;
        }}
        
        .tab:hover {{
            color: #e2e8f0;
            background: rgba(148, 163, 184, 0.1);
        }}
        
        .tab.active {{
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        }}
        
        .tab-content {{
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
        }}
        
        .chart-container {{
            display: none;
        }}
        
        .chart-container.active {{
            display: block;
        }}
        
        footer {{
            text-align: center;
            padding: 2rem;
            margin-top: 2rem;
            border-top: 1px solid rgba(148, 163, 184, 0.1);
            color: #64748b;
            font-size: 0.9rem;
        }}
        
        footer a {{
            color: #60a5fa;
            text-decoration: none;
        }}
        
        footer a:hover {{
            text-decoration: underline;
        }}
        
        .data-sources {{
            margin-top: 1rem;
            font-size: 0.8rem;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}
            
            .tabs {{
                flex-direction: column;
            }}
            
            .stat-value {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header>
            <h1>✈️ US Holiday Travel Dashboard</h1>
            <p class="subtitle">Exploring travel patterns, flight delays, and weather across America</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_passengers / 1_000_000:.1f}M</div>
                <div class="stat-label">Total Holiday Travelers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{avg_delay:.1f}%</div>
                <div class="stat-label">Avg Flight Delay Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{warmest_state['state_name']}</div>
                <div class="stat-label">Warmest State ({warmest_state['avg_dec_temperature']:.0f}°F)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{busiest_state['state_name']}</div>
                <div class="stat-label">Busiest for Travel</div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('travel')">
                🗺️ Travel Volume
            </button>
            <button class="tab" onclick="showTab('delays')">
                ⏱️ Flight Delays
            </button>
            <button class="tab" onclick="showTab('weather')">
                🌡️ December Weather
            </button>
        </div>
        
        <div class="tab-content">
            <div id="travel" class="chart-container active">
                <div id="travel-chart" style="width:100%; height:500px;"></div>
            </div>
            <div id="delays" class="chart-container">
                <div id="delays-chart" style="width:100%; height:500px;"></div>
            </div>
            <div id="weather" class="chart-container">
                <div id="weather-chart" style="width:100%; height:500px;"></div>
            </div>
        </div>
        
        <footer>
            <p>Dashboard created for US Holiday Travel Analysis</p>
            <div class="data-sources">
                <p>Data Sources: 
                    <a href="https://www.bts.gov/" target="_blank">Bureau of Transportation Statistics</a> | 
                    <a href="https://www.ncei.noaa.gov/" target="_blank">NOAA Climate Data</a>
                </p>
                <p>November-December 2024 | Temperature data averaged 2020-2024</p>
            </div>
        </footer>
    </div>
    
    <script>
        // Chart data
        var travelData = {travel_json};
        var delaysData = {delay_json};
        var weatherData = {temp_json};
        
        // Initialize charts on load
        window.addEventListener('load', function() {{
            Plotly.newPlot('travel-chart', travelData.data, travelData.layout, {{responsive: true}});
            Plotly.newPlot('delays-chart', delaysData.data, delaysData.layout, {{responsive: true}});
            Plotly.newPlot('weather-chart', weatherData.data, weatherData.layout, {{responsive: true}});
        }});
        
        function showTab(tabId) {{
            // Hide all containers
            document.querySelectorAll('.chart-container').forEach(container => {{
                container.classList.remove('active');
            }});
            
            // Deactivate all tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Show selected container
            document.getElementById(tabId).classList.add('active');
            
            // Activate selected tab
            event.target.classList.add('active');
            
            // Resize the chart in the newly visible container
            var chartId = tabId + '-chart';
            Plotly.Plots.resize(document.getElementById(chartId));
        }}
    </script>
</body>
</html>'''
    
    return html_template


def main():
    """Main function to run the analysis pipeline."""
    print("=" * 60)
    print("US Holiday Travel Dashboard - Data Analysis")
    print("=" * 60)
    
    # Define data paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, 'data')
    
    # Load all datasets
    temp_df = load_noaa_temperature_data(os.path.join(data_path, 'climdiv-tmpcst.txt'))
    passengers_df = load_airport_passengers(os.path.join(data_path, 'airport_passengers.csv'))
    delays_df = load_flight_delays(os.path.join(data_path, 'flight_delays.csv'))
    
    # Combine datasets
    combined_df = combine_datasets(passengers_df, delays_df, temp_df)
    
    # Save combined data
    output_csv = os.path.join(data_path, 'combined_state_data.csv')
    combined_df.to_csv(output_csv, index=False)
    print(f"\nSaved combined data to: {output_csv}")
    
    # Display summary
    print("\n" + "=" * 60)
    print("Data Summary")
    print("=" * 60)
    print(combined_df[['state_code', 'state_name', 'holiday_travel_volume', 
                       'avg_delay_pct', 'avg_dec_temperature']].to_string(index=False))
    
    # Create visualizations
    print("\n" + "=" * 60)
    print("Creating Visualizations...")
    print("=" * 60)
    
    travel_fig = create_travel_volume_map(combined_df)
    delay_fig = create_delay_map(combined_df)
    temp_fig = create_temperature_map(combined_df)
    
    # Generate HTML dashboard
    print("\nGenerating HTML dashboard...")
    dashboard_html = create_dashboard_html(travel_fig, delay_fig, temp_fig, combined_df)
    
    # Save dashboard
    dashboard_path = os.path.join(base_path, 'holiday_dashboard.html')
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print(f"Dashboard saved to: {dashboard_path}")
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    print("=" * 60)
    
    return combined_df


if __name__ == '__main__':
    main()


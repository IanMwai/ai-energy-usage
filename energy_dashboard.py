import streamlit as st
import os
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

from dotenv import load_dotenv
# Load variables from .env file
load_dotenv()

# Read the API key
API_KEY = os.getenv("API_KEY")

# Set headers
headers = {
    "auth-token": API_KEY,
    "Content-Type": "application/json"
}

# Kenya's typical energy mix (fallback data based on recent reports)
KENYA_ENERGY_MIX = {
    "Hydro": 36.2,
    "Geothermal": 31.1,
    "Thermal (Oil/Gas)": 12.7,
    "Wind": 8.9,
    "Solar": 6.8,
    "Biomass": 2.1,
    "Battery Storage": 1.2,
    "Imports": 1.0
}

def get_kenya_power_data():
    """Try to fetch real data, fallback to static data if API fails"""
    try:
        url = "https://api.electricitymaps.com/v3/power-breakdown/latest"
        params = {"zone": "KE"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'powerProductionBreakdown' in data:
                return data, True
        
        # If API fails, return None to use fallback data
        return None, False
        
    except Exception as e:
        st.warning(f"Live data unavailable: {str(e)}")
        return None, False

def process_kenya_data(api_data=None, use_live=False):
    """Process Kenya power data with proper source mapping"""
    
    source_mappings = {
        'hydro': 'Hydro',
        'geothermal': 'Geothermal', 
        'oil': 'Thermal (Oil)',
        'gas': 'Natural Gas',
        'wind': 'Wind',
        'solar': 'Solar',
        'biomass': 'Biomass',
        'battery': 'Battery Storage',
        'coal': 'Coal',
        'nuclear': 'Nuclear',
        'unknown': 'Other'
    }
    
    if use_live and api_data and 'powerProductionBreakdown' in api_data:
        # Use live API data
        mix = api_data['powerProductionBreakdown']
        timestamp = api_data.get('datetime', datetime.now().isoformat())
        
        records = []
        total = 0
        
        for source, value in mix.items():
            if value is not None and value > 0:
                display_name = source_mappings.get(source, source.title())
                records.append({
                    "source": display_name,
                    "value": value,
                    "percentage": 0  # Will calculate later
                })
                total += value
        
        # Calculate percentages
        for record in records:
            record["percentage"] = (record["value"] / total * 100) if total > 0 else 0
            
        return records, timestamp, total, "Live Data"
    
    else:
        # Use fallback data
        records = []
        total = sum(KENYA_ENERGY_MIX.values())
        
        for source, percentage in KENYA_ENERGY_MIX.items():
            # Convert percentage to approximate MW (Kenya's total capacity ~3000 MW)
            estimated_mw = (percentage / 100) * 2800
            records.append({
                "source": source,
                "value": estimated_mw,
                "percentage": percentage
            })
        
        timestamp = datetime.now().isoformat()
        return records, timestamp, total * 28, "Estimated Data"

def create_kenya_insights():
    """Create educational content about Kenya's power sector"""
    
    st.markdown("""
    ### Kenya's Energy Landscape
    
    Kenya is a leader in renewable energy in Africa, with over **90% renewable electricity generation**:
    
    **Key Facts:**
    - **World's 8th largest geothermal producer**
    - **Abundant hydro resources** from rivers and dams
    - **Rapidly growing solar sector** with excellent solar irradiation
    - **Strong wind resources** especially around Lake Turkana
    - **Target**: 100% renewable electricity by 2030
    """)
    
    # Kenya energy timeline
    timeline_data = {
        "Year": [2014, 2016, 2018, 2020, 2022, 2024],
        "Renewable %": [68, 75, 83, 87, 92, 95],
        "Total Capacity (MW)": [2000, 2300, 2700, 2900, 3100, 3300]
    }
    
    timeline_df = pd.DataFrame(timeline_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_timeline = px.line(
            timeline_df, 
            x="Year", 
            y="Renewable %",
            title="Kenya's Renewable Energy Progress",
            markers=True,
            color_discrete_sequence=["#2E8B57"]
        )
        fig_timeline.update_layout(yaxis_title="Renewable Energy (%)")
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col2:
        fig_capacity = px.bar(
            timeline_df,
            x="Year",
            y="Total Capacity (MW)",
            title="Total Generation Capacity Growth",
            color_discrete_sequence=["#FF6B35"]
        )
        st.plotly_chart(fig_capacity, use_container_width=True)

def display_source_details():
    """Display detailed information about each energy source in Kenya"""
    
    source_info = {
        "Hydro": {
            "capacity": "826 MW",
            "key_plants": "Seven Forks Cascade, Turkwel, Sondu Miriu",
            "challenge": "Seasonal rainfall dependency",
            "advantage": "Reliable baseload power"
        },
        "Geothermal": {
            "capacity": "863 MW", 
            "key_plants": "Olkaria I-VI, Eburru",
            "challenge": "High upfront investment",
            "advantage": "24/7 reliable clean energy"
        },
        "Wind": {
            "capacity": "436 MW",
            "key_plants": "Lake Turkana Wind Power (310 MW)",
            "challenge": "Transmission to population centers", 
            "advantage": "Excellent wind speeds (8-11 m/s)"
        },
        "Solar": {
            "capacity": "173 MW",
            "key_plants": "Garissa Solar (50 MW), Eldosol (40 MW)",
            "challenge": "Grid stability and storage",
            "advantage": "Abundant sunshine year-round"
        }
    }
    
    st.subheader("Energy Source Deep Dive")
    
    for source, info in source_info.items():
        with st.expander(f"{source} - {info['capacity']} installed"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Key Plants:** {info['key_plants']}")
                st.write(f"**Main Challenge:** {info['challenge']}")
            
            with col2:
                st.write(f"**Key Advantage:** {info['advantage']}")

# Main Streamlit App
st.set_page_config(
    page_title="Kenya Energy Dashboard", 
    page_icon="⚡", 
    layout="wide"
)

st.title("Kenya Electricity Generation Dashboard")
st.markdown("*Exploring Kenya's renewable energy leadership in Africa*")

# Try to get live data
with st.spinner("Fetching Kenya electricity data..."):
    api_data, has_live_data = get_kenya_power_data()

# Process the data
records, timestamp, total_mw, data_source = process_kenya_data(api_data, has_live_data)

# Main dashboard
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # Main pie chart
    if records:
        df = pd.DataFrame(records)
        
        # Custom colors for Kenya energy sources
        colors = {
            'Hydro': '#1f77b4',
            'Geothermal': '#ff7f0e', 
            'Thermal (Oil/Gas)': '#d62728',
            'Thermal (Oil)': '#d62728',
            'Natural Gas': '#ff6b6b',
            'Wind': '#2ca02c',
            'Solar': '#ffbb33',
            'Biomass': '#8c564b',
            'Battery Storage': '#9467bd',
            'Imports': '#17becf',
            'Other': '#bcbd22'
        }
        
        fig = px.pie(
            df, 
            values='percentage', 
            names='source',
            title=f"Current Energy Mix ({data_source})",
            hole=0.4,
            color='source',
            color_discrete_map=colors
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Share: %{percent}<br>Generation: %{value:.0f}%<extra></extra>'
        )
        
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric(
        label="Total Generation", 
        value=f"{total_mw:.0f} MW",
        help="Current total electricity generation"
    )
    
    # Calculate renewable percentage
    renewable_sources = ['Hydro', 'Geothermal', 'Wind', 'Solar', 'Biomass']
    renewable_pct = sum([r['percentage'] for r in records if r['source'] in renewable_sources])
    
    st.metric(
        label="Renewable Share",
        value=f"{renewable_pct:.1f}%",
        delta="World leader!",
        help="Percentage from renewable sources"
    )

with col3:
    st.metric(
        label="Data Source",
        value=data_source,
        help="Whether using live or estimated data"
    )
    
    st.metric(
        label="Last Updated",
        value=datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%H:%M') if 'T' in timestamp else "Recent",
        help="When the data was last refreshed"
    )

# Data table
st.subheader("Detailed Breakdown")
if records:
    display_df = pd.DataFrame(records)
    display_df['Generation (MW)'] = display_df['value'].round(0)
    display_df['Share (%)'] = display_df['percentage'].round(1)
    
    # Sort by percentage
    display_df = display_df.sort_values('percentage', ascending=False)
    
    st.dataframe(
        display_df[['source', 'Share (%)', 'Generation (MW)']].rename(columns={'source': 'Energy Source'}),
        use_container_width=True,
        hide_index=True
    )

# Educational content
create_kenya_insights()
display_source_details()

# Regional comparison
st.subheader("Kenya vs. Regional Averages")

comparison_data = {
    'Region': ['Kenya', 'East Africa Avg', 'Sub-Saharan Africa', 'Global Average'],
    'Renewable Share (%)': [92, 65, 45, 29],
    'Access Rate (%)': [75, 45, 48, 90]
}

comparison_df = pd.DataFrame(comparison_data)

fig_comparison = px.bar(
    comparison_df,
    x='Region',
    y='Renewable Share (%)',
    title="Renewable Energy Share Comparison",
    color='Renewable Share (%)',
    color_continuous_scale='Greens'
)

st.plotly_chart(fig_comparison, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    f"""
    **Data Sources:** Kenya Power & Lighting Company, Ministry of Energy, Electricity Maps  
    **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
    **Note:** {data_source} - Live data may be unavailable due to API limitations
    """
)

with st.expander("About Kenya's Energy Sector"):
    st.markdown("""
    Kenya is recognized globally as a renewable energy leader, particularly in:
    
    - **Geothermal Energy**: The Rift Valley contains some of the world's best geothermal resources
    - **Hydro Power**: Multiple dam systems provide consistent clean energy
    - **Wind Power**: Lake Turkana hosts Africa's largest wind farm (310 MW)
    - **Solar Potential**: Excellent solar irradiation levels across the country
    
    **Future Projects:**
    - Additional geothermal plants in the Rift Valley
    - More wind farms in northern Kenya  
    - Distributed solar systems and mini-grids
    - Regional power trading with neighboring countries
    """)
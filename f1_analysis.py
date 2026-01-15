import streamlit as st
import fastf1
import pandas as pd
import os

# 1. Page Config
st.set_page_config(page_title="F1 Telemetry Analyst", layout="wide")

# 2. Setup (Cache Only - No Matplotlib setup needed)
@st.cache_resource
def setup_f1():
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    fastf1.Cache.enable_cache(cache_dir)

setup_f1()

# 3. Sidebar
st.sidebar.title("🏎️ F1 Deep Dive (Lightweight)")
year = st.sidebar.selectbox("Year", [2024, 2023, 2022], index=1)
gp = st.sidebar.selectbox("Grand Prix", ["Monaco", "Bahrain", "Silverstone", "Monza"], index=0)
session_type = st.sidebar.radio("Session", ["Q", "R"], format_func=lambda x: "Qualifying" if x == "Q" else "Race")

col1, col2 = st.sidebar.columns(2)
d1 = col1.text_input("Driver 1", "VER")
d2 = col2.text_input("Driver 2", "LEC")

# 4. Analysis
st.title(f"🏁 {year} {gp} - Native Analysis")

if st.sidebar.button("Analyze Telemetry"):
    try:
        with st.spinner(f"Pulling telemetry for {d1} vs {d2}..."):
            
            # Load Session
            session = fastf1.get_session(year, gp, session_type)
            session.load(telemetry=True, weather=False, messages=False)
            
            # Pick Fastest Laps
            laps = session.laps.pick_drivers([d1, d2])
            d1_lap = laps.pick_drivers(d1).pick_fastest()
            d2_lap = laps.pick_drivers(d2).pick_fastest()
            
            # Telemetry
            d1_tel = d1_lap.get_car_data().add_distance()
            d2_tel = d2_lap.get_car_data().add_distance()
            
            # --- DEBUG: CHECK DATA ---
            # If this prints 0, we know the data is empty!
            st.write(f"DEBUG: Found {len(d1_tel)} data points for {d1}")
            
            # --- PREPARE DATA FOR NATIVE CHARTS ---
            # Streamlit needs a single dataframe with columns: [Distance, Speed_VER, Speed_LEC]
            
            # 1. Rename columns to identify drivers
            d1_df = d1_tel[['Distance', 'Speed', 'Throttle', 'Brake']].copy()
            d1_df.columns = ['Distance', f'Speed {d1}', f'Throttle {d1}', f'Brake {d1}']
            
            d2_df = d2_tel[['Distance', 'Speed', 'Throttle', 'Brake']].copy()
            d2_df.columns = ['Distance', f'Speed {d2}', f'Throttle {d2}', f'Brake {d2}']
            
            # 2. Merge them on Distance (approximate)
            # We align them by index for a rough "overlay" since distances never match perfectly
            # A simple way for MVP: Just plot them independently on same chart
            
            st.subheader("🚀 Speed Trace")
            # We create a combined chart manually using line_chart
            chart_data = pd.DataFrame({
                f"{d1} Speed": d1_tel['Speed'].values,
                f"{d2} Speed": d2_tel['Speed'].values
            })
            st.line_chart(chart_data, color=["#0000FF", "#FF0000"]) # Blue vs Red

            st.subheader("🦶 Throttle Trace")
            throttle_data = pd.DataFrame({
                f"{d1} Throttle": d1_tel['Throttle'].values,
                f"{d2} Throttle": d2_tel['Throttle'].values
            })
            st.line_chart(throttle_data, color=["#0000FF", "#FF0000"])

            # Metrics
            delta = d1_lap['LapTime'] - d2_lap['LapTime']
            st.success(f"Gap: {delta.total_seconds():.3f}s")

    except Exception as e:
        st.error(f"Error: {e}")
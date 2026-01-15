import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt

# 1. Page Config (The title of your website tab)
st.set_page_config(page_title="F1 Telemetry Analyzer", layout="wide")

# 2. Setup (Cache and Plotting)
# We use @st.cache_data so it doesn't redownload data every time you click a button
@st.cache_resource
def setup_f1():
    fastf1.Cache.enable_cache('cache')
    fastf1.plotting.setup_mpl()

setup_f1()

# 3. The Sidebar (User Inputs)
st.sidebar.title("🏎️ F1 Telemetry Tool")
st.sidebar.markdown("Compare two drivers' fastest laps.")

# Dropdowns for Year and Grand Prix
year = st.sidebar.selectbox("Year", [2023, 2022, 2021], index=0)
gp = st.sidebar.selectbox("Grand Prix", ["Monaco", "Bahrain", "Silverstone", "Monza"], index=0)
session_type = st.sidebar.radio("Session", ["Q", "R"], format_func=lambda x: "Qualifying" if x == "Q" else "Race")

# Driver Inputs (Hardcoded for now, we can make this dynamic later)
d1 = st.sidebar.text_input("Driver 1 (3 letter code)", "VER")
d2 = st.sidebar.text_input("Driver 2 (3 letter code)", "LEC")

# 4. The Main App Logic
st.title(f"🏁 {year} {gp} Analysis")

if st.sidebar.button("Analyze Telemetry"):
    try:
        with st.spinner(f"Downloading data for {gp}..."):
            # Load Session
            session = fastf1.get_session(year, gp, session_type)
            session.load()
            
            # Pick Drivers
            d1_lap = session.laps.pick_drivers(d1).pick_fastest()
            d2_lap = session.laps.pick_drivers(d2).pick_fastest()
            
            # Telemetry
            d1_tel = d1_lap.get_car_data().add_distance()
            d2_tel = d2_lap.get_car_data().add_distance()
            
            # Delta
            delta = d1_lap['LapTime'] - d2_lap['LapTime']
            gap = delta.total_seconds()
            
            # Display Metrics
            col1, col2 = st.columns(2)
            col1.metric(f"{d1} Lap Time", str(d1_lap['LapTime']).split('days')[-1].strip(), delta_color="normal")
            col2.metric(f"{d2} Lap Time", str(d2_lap['LapTime']).split('days')[-1].strip(), f"{gap:.3f}s")
            
            # Plotting
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Colors
            d1_color = fastf1.plotting.get_driver_color(d1, session=session)
            d2_color = fastf1.plotting.get_driver_color(d2, session=session)
            
            ax.plot(d1_tel['Distance'], d1_tel['Speed'], color=d1_color, label=d1)
            ax.plot(d2_tel['Distance'], d2_tel['Speed'], color=d2_color, label=d2, linestyle='--')
            
            ax.set_xlabel("Distance (m)")
            ax.set_ylabel("Speed (km/h)")
            ax.legend()
            
            # THE MAGIC LINE: Send the plot to the website
            st.pyplot(fig)
            
    except Exception as e:
        st.error(f"Error: {e}")
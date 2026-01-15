import streamlit as st
import pandas as pd
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import os

# 1. Page Config
st.set_page_config(page_title="F1 Telemetry Analyst", layout="wide")

# 2. Setup (Self-Healing Cache)
@st.cache_resource
def setup_f1():
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    fastf1.Cache.enable_cache(cache_dir)
    # We use the 'fastf1' plotting style for that cool dark look
    try:
        fastf1.plotting.setup_mpl()
    except Exception:
        pass

setup_f1()

# 3. Sidebar
st.sidebar.title("🏎️ F1 Deep Dive")
year = st.sidebar.selectbox("Year", [2023, 2022], index=0)
gp = st.sidebar.selectbox("Grand Prix", ["Monaco", "Bahrain", "Silverstone", "Monza"], index=0)
session_type = st.sidebar.radio("Session", ["Q", "R"], format_func=lambda x: "Qualifying" if x == "Q" else "Race")

col1, col2 = st.sidebar.columns(2)
d1 = col1.text_input("Driver 1", "VER")
d2 = col2.text_input("Driver 2", "LEC")

# 4. Main Analysis
st.title(f"🏁 {year} {gp} - Driver Input Analysis")

if st.sidebar.button("Analyze Telemetry"):
    try:
        with st.spinner(f"Processing data for {d1} vs {d2}..."):
            
            # Load Session (Lightweight)
            session = fastf1.get_session(year, gp, session_type)
            session.load(telemetry=True, weather=False, messages=False)
            
            # Pick Laps
            laps = session.laps.pick_drivers([d1, d2])
            d1_lap = laps.pick_drivers(d1).pick_fastest()
            d2_lap = laps.pick_drivers(d2).pick_fastest()
            
            # --- THE GOLDEN FIX: DOWNSAMPLING ---
            # We take every 8th data point (iloc[::8]). 
            # This reduces 5000 points -> 600 points. Fast & Stable.
            d1_tel = d1_lap.get_car_data().add_distance().iloc[::8]
            d2_tel = d2_lap.get_car_data().add_distance().iloc[::8]
            
            # Metrics
            delta = d1_lap['LapTime'] - d2_lap['LapTime']
            gap = delta.total_seconds()
            winner = d1 if gap < 0 else d2
            
            # Display Metrics
            m1, m2 = st.columns(2)
            m1.metric("Pole/Winner", winner)
            m2.metric("Gap", f"{abs(gap):.3f}s")

            # --- PLOTTING (Matplotlib) ---
            # Now safe to use because data is small!
            fig, ax = plt.subplots(3, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [3, 1, 1]}, sharex=True)
            
            c1 = fastf1.plotting.get_driver_color(d1, session=session)
            c2 = fastf1.plotting.get_driver_color(d2, session=session)

            # 1. Speed Trace
            ax[0].plot(d1_tel['Distance'], d1_tel['Speed'], color=c1, label=d1)
            ax[0].plot(d2_tel['Distance'], d2_tel['Speed'], color=c2, label=d2, linestyle='--')
            ax[0].set_ylabel("Speed (km/h)")
            ax[0].legend(loc="lower right")
            ax[0].set_title("Speed Trace")

            # 2. Throttle Trace
            ax[1].plot(d1_tel['Distance'], d1_tel['Throttle'], color=c1, label=d1)
            ax[1].plot(d2_tel['Distance'], d2_tel['Throttle'], color=c2, label=d2, linestyle='--')
            ax[1].set_ylabel("Throttle %")
            ax[1].set_ylim(-5, 105) 

            # 3. Brake Trace
            ax[2].plot(d1_tel['Distance'], d1_tel['Brake'], color=c1, label=d1)
            ax[2].plot(d2_tel['Distance'], d2_tel['Brake'], color=c2, label=d2, linestyle='--')
            ax[2].set_ylabel("Brake")
            ax[2].set_xlabel("Distance (m)")

            # Clean up axes
            for a in ax[:-1]:
                a.tick_params(labelbottom=False)

            st.pyplot(fig)
            
    except KeyError:
        st.error(f"Driver not found! Check if {d1} or {d2} raced.")
    except Exception as e:
        st.error(f"Error: {e}")
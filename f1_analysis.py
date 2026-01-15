import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="F1 Telemetry Analyst", layout="wide")

# 2. Setup (Cache and Plotting)
@st.cache_resource
def setup_f1():
    fastf1.Cache.enable_cache('cache')
    fastf1.plotting.setup_mpl()

setup_f1()

# 3. Sidebar Configuration
st.sidebar.title("🏎️ F1 Deep Dive")
st.sidebar.markdown("Compare driver inputs to find time.")

# Selection UI
year = st.sidebar.selectbox("Year", [2024, 2023, 2022], index=1)
gp = st.sidebar.selectbox("Grand Prix", ["Monaco", "Bahrain", "Silverstone", "Monza", "Suzuka"], index=0)
session_type = st.sidebar.radio("Session", ["Q", "R"], format_func=lambda x: "Qualifying" if x == "Q" else "Race")

col1, col2 = st.sidebar.columns(2)
d1 = col1.text_input("Driver 1", "VER")
d2 = col2.text_input("Driver 2", "LEC")

# 4. Main Analysis Logic
st.title(f"🏁 {year} {gp} - Driver Input Analysis")

if st.sidebar.button("Analyze Telemetry"):
    try:
        with st.spinner(f"Pulling telemetry for {d1} vs {d2}..."):
            # Load Session
            session = fastf1.get_session(year, gp, session_type)
            session.load()
            
            # Pick Fastest Laps
            laps = session.laps.pick_drivers([d1, d2])
            d1_lap = laps.pick_driver(d1).pick_fastest()
            d2_lap = laps.pick_driver(d2).pick_fastest()
            
            # Get Telemetry
            d1_tel = d1_lap.get_car_data().add_distance()
            d2_tel = d2_lap.get_car_data().add_distance()
            
            # Metric Calculation
            delta_time = d1_lap['LapTime'] - d2_lap['LapTime']
            gap = delta_time.total_seconds()
            winner = d1 if gap < 0 else d2
            
            # --- DASHBOARD METRICS ---
            m1, m2, m3 = st.columns(3)
            m1.metric("Pole/Winner", winner)
            m2.metric(f"Gap", f"{abs(gap):.3f}s")
            m3.metric("Track Temp", f"{session.weather_data.iloc[0]['TrackTemp']}°C")

            # --- PLOTTING (The Upgrade) ---
            # We create 3 subplots sharing the X-axis (Distance)
            fig, ax = plt.subplots(3, 1, figsize=(12, 12), gridspec_kw={'height_ratios': [3, 1, 1]}, sharex=True)
            
            # Colors
            c1 = fastf1.plotting.get_driver_color(d1, session=session)
            c2 = fastf1.plotting.get_driver_color(d2, session=session)

            # 1. Speed Trace (Top)
            ax[0].plot(d1_tel['Distance'], d1_tel['Speed'], color=c1, label=d1)
            ax[0].plot(d2_tel['Distance'], d2_tel['Speed'], color=c2, label=d2, linestyle='--')
            ax[0].set_ylabel("Speed (km/h)")
            ax[0].legend(loc="lower right")
            ax[0].set_title("Speed Trace")

            # 2. Throttle Trace (Middle)
            ax[1].plot(d1_tel['Distance'], d1_tel['Throttle'], color=c1, label=d1)
            ax[1].plot(d2_tel['Distance'], d2_tel['Throttle'], color=c2, label=d2, linestyle='--')
            ax[1].set_ylabel("Throttle %")
            ax[1].set_ylim(-5, 105) # Keep it fixed 0-100
            ax[1].set_title("Throttle Application")

            # 3. Brake Trace (Bottom)
            # Use 'Brake' column (0 or 1 usually, or pressure)
            ax[2].plot(d1_tel['Distance'], d1_tel['Brake'], color=c1, label=d1)
            ax[2].plot(d2_tel['Distance'], d2_tel['Brake'], color=c2, label=d2, linestyle='--')
            ax[2].set_ylabel("Brake (On/Off)")
            ax[2].set_title("Braking Points")
            ax[2].set_xlabel("Distance (m)")

            # Hide x-labels for top plots to look cleaner
            for a in ax[:-1]:
                a.tick_params(labelbottom=False)

            st.pyplot(fig)
            
            # --- AI INSIGHT (Simple Rule-Based) ---
            st.subheader("💡 Automated Insights")
            d1_top_speed = d1_tel['Speed'].max()
            d2_top_speed = d2_tel['Speed'].max()
            
            if d1_top_speed > d2_top_speed:
                st.write(f"🚀 **Top Speed King:** {d1} hit **{d1_top_speed} km/h**, which is {d1_top_speed - d2_top_speed:.1f} km/h faster than {d2}. This suggests lower drag setup.")
            else:
                st.write(f"🚀 **Top Speed King:** {d2} hit **{d2_top_speed} km/h**, faster than {d1}.")

    except Exception as e:
        st.error(f"Error: {e}")
        st.write("Tip: Check if the drivers participated in this session!")
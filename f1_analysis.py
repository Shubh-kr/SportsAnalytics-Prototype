import streamlit as st
import pandas as pd
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap
import numpy as np
import os

# 1. Page Config
st.set_page_config(page_title="F1 Telemetry Analyst", layout="wide")

# 2. Setup
@st.cache_resource
def setup_f1():
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    fastf1.Cache.enable_cache(cache_dir)
    try:
        fastf1.plotting.setup_mpl()
    except Exception:
        pass

setup_f1()

# 3. Helper Function: Draw the Speed Map
# This function takes telemetry and draws the colored track
def plot_speed_map(lap, driver_code):
    # Get telemetry data (x, y, speed)
    tel = lap.get_telemetry()
    x = np.array(tel['X'].values)
    y = np.array(tel['Y'].values)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Color the line by Speed
    cmap = plt.get_cmap('plasma') # 'plasma' is a cool purple-to-yellow heatmap
    norm = plt.Normalize(tel['Speed'].min(), tel['Speed'].max())
    lc = LineCollection(segments, cmap=cmap, norm=norm, linestyle='-', linewidth=5)
    lc.set_array(tel['Speed'])
    
    # Add to plot
    line = ax.add_collection(lc)
    fig.colorbar(line, ax=ax, label="Speed (km/h)")
    
    # Styling (Hide axes for a clean map look)
    ax.set_xlim(x.min()-200, x.max()+200)
    ax.set_ylim(y.min()-200, y.max()+200)
    ax.axis('off')
    ax.set_title(f"{driver_code} - Speed Map")
    
    return fig

# 4. Sidebar
st.sidebar.title("🏎️ F1 Deep Dive")
year = st.sidebar.selectbox("Year", [2023, 2022], index=0)
gp = st.sidebar.selectbox("Grand Prix", ["Monaco", "Bahrain", "Silverstone", "Monza"], index=0)
session_type = st.sidebar.radio("Session", ["Q", "R"], format_func=lambda x: "Qualifying" if x == "Q" else "Race")

col1, col2 = st.sidebar.columns(2)
d1 = col1.text_input("Driver 1", "VER")
d2 = col2.text_input("Driver 2", "LEC")

# 5. Main Analysis
st.title(f"🏁 {year} {gp} - Data Deep Dive")

if st.sidebar.button("Analyze Telemetry"):
    try:
        with st.spinner(f"Processing data for {d1} vs {d2}..."):
            
            # Load Session
            session = fastf1.get_session(year, gp, session_type)
            session.load(telemetry=True, weather=False, messages=False)
            
            # Pick Laps
            laps = session.laps.pick_drivers([d1, d2])
            d1_lap = laps.pick_drivers(d1).pick_fastest()
            d2_lap = laps.pick_drivers(d2).pick_fastest()
            
            # --- TAB LAYOUT (New!) ---
            # We split the analysis into two tabs: "Traces" and "Track Map"
            tab1, tab2 = st.tabs(["📈 Telemetry Traces", "🗺️ Speed Visualization"])
            
            with tab1:
                st.header("Telemetry Comparison")
                # Downsampling for stability
                d1_tel = d1_lap.get_car_data().add_distance().iloc[::8]
                d2_tel = d2_lap.get_car_data().add_distance().iloc[::8]
                
                # Metrics
                delta = d1_lap['LapTime'] - d2_lap['LapTime']
                gap = delta.total_seconds()
                winner = d1 if gap < 0 else d2
                st.info(f"Winner: **{winner}** by {abs(gap):.3f}s")

                # Plot Traces
                fig, ax = plt.subplots(3, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [3, 1, 1]}, sharex=True)
                c1 = fastf1.plotting.get_driver_color(d1, session=session)
                c2 = fastf1.plotting.get_driver_color(d2, session=session)
                
                # Speed
                ax[0].plot(d1_tel['Distance'], d1_tel['Speed'], color=c1, label=d1)
                ax[0].plot(d2_tel['Distance'], d2_tel['Speed'], color=c2, label=d2, linestyle='--')
                ax[0].set_ylabel("Speed (km/h)")
                ax[0].legend(loc="lower right")
                
                # Throttle
                ax[1].plot(d1_tel['Distance'], d1_tel['Throttle'], color=c1, label=d1)
                ax[1].plot(d2_tel['Distance'], d2_tel['Throttle'], color=c2, label=d2, linestyle='--')
                ax[1].set_ylabel("Throttle %")
                
                # Brake
                ax[2].plot(d1_tel['Distance'], d1_tel['Brake'], color=c1, label=d1)
                ax[2].plot(d2_tel['Distance'], d2_tel['Brake'], color=c2, label=d2, linestyle='--')
                ax[2].set_ylabel("Brake")
                
                for a in ax[:-1]: a.tick_params(labelbottom=False)
                st.pyplot(fig)

            with tab2:
                st.header(f"Track Speed Heatmap ({d1})")
                st.write("Warmer colors (Yellow/Red) = Higher Speed. Cooler colors (Purple) = Slower.")
                # We only plot the map for the winner/Driver 1 to save memory
                fig_map = plot_speed_map(d1_lap, d1)
                st.pyplot(fig_map)

    except Exception as e:
        st.error(f"Error: {e}")
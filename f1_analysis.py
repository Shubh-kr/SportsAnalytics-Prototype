import streamlit as st
import pandas as pd
import os

# 1. Page Config
st.set_page_config(page_title="F1 Diagnostics", layout="centered")

st.title("🛠️ F1 App Diagnostics")
st.write("Step 1: App started. Importing libraries...")

try:
    import fastf1
    st.write("Step 2: FastF1 imported successfully.")
except Exception as e:
    st.error(f"CRITICAL ERROR: Could not import FastF1. {e}")
    st.stop()

# 2. Cache Setup
try:
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    fastf1.Cache.enable_cache(cache_dir)
    st.write("Step 3: Cache directory setup complete.")
except Exception as e:
    st.warning(f"Cache warning (non-fatal): {e}")

# 3. Sidebar
st.sidebar.header("Settings")
year = st.sidebar.selectbox("Year", [2023], index=0)
gp = st.sidebar.selectbox("Grand Prix", ["Monaco", "Bahrain"], index=0)
d1 = st.sidebar.text_input("Driver", "VER")

if st.sidebar.button("Run Diagnostics"):
    st.write("Step 4: Button clicked. Attempting to download data...")
    
    try:
        with st.spinner("Downloading..."):
            # Load Session
            session = fastf1.get_session(year, gp, 'Q')
            
            # LIGHTWEIGHT LOAD: We only load what we absolutely need
            st.write("Step 5: Session object created. Loading data...")
            session.load(telemetry=True, weather=False, messages=False)
            st.write("Step 6: Data loaded from F1 servers.")
            
            # Pick Lap
            lap = session.laps.pick_drivers(d1).pick_fastest()
            st.write(f"Step 7: Fastest lap found for {d1}: {lap['LapTime']}")
            
            # Get Telemetry
            tel = lap.get_car_data().add_distance()
            raw_count = len(tel)
            st.write(f"Step 8: Raw telemetry has {raw_count} points.")
            
            # DOWNSAMPLING (The Fix?)
            # Take every 10th point to save memory
            tel_small = tel.iloc[::10]
            st.write(f"Step 9: Downsampled to {len(tel_small)} points for plotting.")
            
            # Plotting
            st.subheader("Test Plot (Speed)")
            st.line_chart(tel_small[['Distance', 'Speed']].set_index('Distance'))
            st.write("Step 10: Plot rendered successfully!")
            
            st.success("Diagnostics Passed! The app is working.")

    except Exception as e:
        st.error(f"CRASH AT STEP X: {e}")
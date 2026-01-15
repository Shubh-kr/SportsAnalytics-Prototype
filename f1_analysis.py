import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt

# 1. Enable the cache (you already created the folder, so this works now!)
fastf1.Cache.enable_cache('cache') 

# 2. Setup the plotting style (Updated for v3.7+)
fastf1.plotting.setup_mpl()

def compare_drivers(year, grand_prix, session_type, driver1_code, driver2_code):
    print(f"Loading {year} {grand_prix}...")
    
    # Load the Session
    session = fastf1.get_session(year, grand_prix, session_type)
    session.load()
    
    # 3. Pick the fastest laps (Updated to use 'pick_drivers')
    d1_lap = session.laps.pick_drivers(driver1_code).pick_fastest()
    d2_lap = session.laps.pick_drivers(driver2_code).pick_fastest()
    
    # Extract Telemetry
    d1_tel = d1_lap.get_car_data().add_distance()
    d2_tel = d2_lap.get_car_data().add_distance()
    
    # Calculate the Gap
    delta_time = d1_lap['LapTime'] - d2_lap['LapTime']
    winner = driver1_code if delta_time.total_seconds() < 0 else driver2_code
    gap = abs(delta_time.total_seconds())
    
    print(f"Stats loaded! {winner} was faster by {gap:.3f} seconds.")
    
    # --- PLOTTING ---
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 4. Get Driver Colors (Updated to use 'get_driver_color' with session)
    d1_color = fastf1.plotting.get_driver_color(driver1_code, session=session)
    d2_color = fastf1.plotting.get_driver_color(driver2_code, session=session)
    
    # Plot Driver 1
    ax.plot(d1_tel['Distance'], d1_tel['Speed'], 
            color=d1_color, 
            label=driver1_code)
    
    # Plot Driver 2
    ax.plot(d2_tel['Distance'], d2_tel['Speed'], 
            color=d2_color, 
            label=driver2_code,
            linestyle='--') 

    ax.set_title(f"{year} {grand_prix} ({session_type}): {driver1_code} vs {driver2_code}")
    ax.set_xlabel("Distance along track (meters)")
    ax.set_ylabel("Speed (km/h)")
    ax.legend()
    
    plt.show()

# Run the comparison
compare_drivers(2023, 'Monaco', 'Q', 'VER', 'LEC')
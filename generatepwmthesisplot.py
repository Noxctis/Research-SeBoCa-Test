import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# ==========================================
# 1. Configuration & Thesis Formatting
# ==========================================
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'lines.linewidth': 1.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

date_str = datetime.now().strftime("%Y%m%d")
output_dir = f"MIXR1_Thesis_Plots_{date_str}"
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory created: {output_dir}/")

file_openloop = "mixr1_log_20260918_121626_256ppr_20ms_15pwm_around350rpm_openlooppwm_around_370_for_baffles.csv"

try:
    df_ol = pd.read_csv(file_openloop)
except FileNotFoundError as e:
    print(f"Error loading CSV file: {e}")
    exit(1)

# ==========================================
# 2. Open-Loop Load Disturbance Overview
# ==========================================
def plot_disturbance_overview():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_ol['t (s)'], df_ol['Filtered RPM'], label='Filtered RPM', color='#1f77b4', alpha=0.9)
    ax.plot(df_ol['t (s)'], df_ol['Raw RPM'], label='Raw RPM', color='gray', alpha=0.3, linewidth=1)

    water_drops = [49, 68, 87, 112, 144]
    for drop in water_drops:
        ax.axvline(drop, color='teal', linestyle=':', linewidth=1.5, label='Water Drop' if drop == 49 else "")

    ax.axvline(371, color='orange', linestyle='--', linewidth=1.5, label='Baffles Inserted')
    ax.axvline(386, color='green', linestyle='--', linewidth=1.5, label='Baffles Removed')

    ax.set_title("Open-Loop Response: Transient Disturbances & Baffle Dynamics")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("RPM")
    ax.set_xlim(0, max(df_ol['t (s)']) + 5)
    ax.set_ylim(-10, 420)
    ax.legend(loc='lower left')
    ax.grid(True, linestyle=':', alpha=0.7)
    
    plt.savefig(os.path.join(output_dir, "fig1_openloop_disturbance_overview.png"))
    plt.close(fig)

# ==========================================
# 3. Isolated Event Zooms
# ==========================================
def plot_isolated_events():
    events = {
        "Drop_1": (49, "teal", ":"),
        "Drop_2": (68, "teal", ":"),
        "Drop_3": (87, "teal", ":"),
        "Drop_4": (112, "teal", ":"),
        "Drop_5": (144, "teal", ":"),
        "Baffle_Insert": (371, "orange", "--"),
        "Baffle_Remove": (386, "green", "--")
    }

    for idx, (event_name, (event_t, color, style)) in enumerate(events.items(), start=2):
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Widened window to capture open-loop exponential recovery settling times
        window_start = event_t - 5
        window_end = event_t + 25 
        df_zoom = df_ol[(df_ol['t (s)'] >= window_start) & (df_ol['t (s)'] <= window_end)]
        
        ax.plot(df_zoom['t (s)'], df_zoom['Raw RPM'], color='gray', alpha=0.4, label='Raw RPM', linewidth=1)
        ax.plot(df_zoom['t (s)'], df_zoom['Filtered RPM'], color='#1f77b4', linewidth=2, label='Filtered RPM')
        
        ax.axvline(event_t, color=color, linestyle=style, linewidth=2, label=event_name.replace("_", " "))
        
        event_title = event_name.replace("_", " ")
        if "Drop" in event_title: 
            event_title = "Water " + event_title
        
        ax.set_title(f"{event_title} Transient Response (t = {event_t}s)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("RPM")
        
        # Dynamically scale Y-axis based on the data in the zoomed window
        y_min = df_zoom['Filtered RPM'].min()
        y_max = df_zoom['Filtered RPM'].max()
        padding = (y_max - y_min) * 0.2 if (y_max - y_min) > 0 else 20
        ax.set_ylim(max(0, y_min - padding), y_max + padding)
            
        ax.legend(loc='best')
        ax.grid(True, linestyle=':', alpha=0.7)
        
        filename = f"fig{idx}_openloop_{event_name.lower()}.png"
        plt.savefig(os.path.join(output_dir, filename))
        plt.close(fig)

# ==========================================
# Execute Script
# ==========================================
if __name__ == "__main__":
    print("Generating open-loop thesis plots...")
    plot_disturbance_overview()
    plot_isolated_events()
    print(f"Complete. All thesis-formatted plots saved to {output_dir}/")
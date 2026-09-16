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

file_05 = "mixr1_log_20260915_120201_256ppr_20ms_350rpm05radsforrealcomplete.csv"
file_10 = "mixr1_log_20260914_185949_350rpm_1rads_pi.csv"
file_dist_10 = "mixr1_log_20260914_185949_350rpm_1rads_pi.csv"

try:
    df_05 = pd.read_csv(file_05)
    df_10 = pd.read_csv(file_10)
    df_dist_10 = pd.read_csv(file_dist_10)
except FileNotFoundError as e:
    print(f"Error loading CSV files: {e}")
    exit(1)

# ==========================================
# 2. Step Response Comparison (Full & Transient)
# ==========================================
def plot_step_responses():
    step_05 = df_05[df_05['Filtered RPM'] > 10]['t (s)'].iloc[0]
    step_10 = df_10[df_10['Filtered RPM'] > 10]['t (s)'].iloc[0]

    df_05_aligned = df_05.copy()
    df_10_aligned = df_10.copy()
    df_05_aligned['t_aligned'] = df_05_aligned['t (s)'] - step_05
    df_10_aligned['t_aligned'] = df_10_aligned['t (s)'] - step_10

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df_05_aligned['t_aligned'], df_05_aligned['Filtered RPM'], label='0.5 rad/s (PI)', alpha=0.8, color='#1f77b4')
    ax.plot(df_10_aligned['t_aligned'], df_10_aligned['Filtered RPM'], label='1.0 rad/s (PI)', alpha=0.8, color='#ff7f0e')
    ax.axhline(350, color='red', linestyle='--', label='Target (350 RPM)')
    ax.set_title("Full Step Response: 0.5 rad/s vs 1.0 rad/s Bandwidth")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Filtered RPM")
    ax.set_xlim(-5, 300)
    ax.legend(loc='lower right')
    ax.grid(True, linestyle=':', alpha=0.7)
    plt.savefig(os.path.join(output_dir, "fig1_step_response_full.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df_05_aligned['t_aligned'], df_05_aligned['Filtered RPM'], label='0.5 rad/s', marker='o', markersize=3, color='#1f77b4')
    ax.plot(df_10_aligned['t_aligned'], df_10_aligned['Filtered RPM'], label='1.0 rad/s', marker='s', markersize=3, color='#ff7f0e')
    ax.axhline(350, color='red', linestyle='--', label='Target (350 RPM)')
    ax.set_title("Transient Response (First 5 Seconds)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Filtered RPM")
    ax.set_xlim(-0.5, 5)
    ax.set_ylim(0, 400)
    ax.legend(loc='lower right')
    ax.grid(True, linestyle=':', alpha=0.7)
    plt.savefig(os.path.join(output_dir, "fig2_step_response_transient.png"))
    plt.close(fig)

# ==========================================
# 3. 1.0 rad/s Load Disturbance Overview
# ==========================================
def plot_disturbance_overview_10():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_dist_10['t (s)'], df_dist_10['Filtered RPM'], label='Filtered RPM', color='#1f77b4', alpha=0.9)
    ax.plot(df_dist_10['t (s)'], df_dist_10['Raw RPM'], label='Raw RPM', color='gray', alpha=0.3, linewidth=1)
    ax.axhline(350, color='red', linestyle='--', label='Target (350 RPM)')

    water_drops = [11, 27, 74, 94, 117]
    for drop in water_drops:
        ax.axvline(drop, color='teal', linestyle=':', linewidth=1.5, label='Water Drop' if drop == 11 else "")

    ax.axvline(147, color='orange', linestyle='--', linewidth=1.5, label='Baffles Inserted')
    ax.axvline(179, color='green', linestyle='--', linewidth=1.5, label='Baffles Removed')

    ax.set_title("1.0 rad/s PI Controller: Full Disturbance Response")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("RPM")
    ax.set_xlim(0, 205)
    ax.set_ylim(-20, 420)
    ax.legend(loc='lower right')
    ax.grid(True, linestyle=':', alpha=0.7)
    plt.savefig(os.path.join(output_dir, "fig3_10rads_disturbance_overview.png"))
    plt.close(fig)

# ==========================================
# 4. 1.0 rad/s Isolated Event Zooms
# ==========================================
def plot_isolated_events_10():
    events = {
        "Drop_1": (11, "teal", ":"),
        "Drop_2": (27, "teal", ":"),
        "Drop_3": (74, "teal", ":"),
        "Drop_4": (94, "teal", ":"),
        "Drop_5": (117, "teal", ":"),
        "Baffle_Insert": (147, "orange", "--"),
        "Baffle_Remove": (179, "green", "--")
    }

    for idx, (event_name, (event_t, color, style)) in enumerate(events.items(), start=4):
        fig, ax = plt.subplots(figsize=(6, 4))
        
        window_start = event_t - 2
        window_end = event_t + 8
        df_zoom = df_dist_10[(df_dist_10['t (s)'] >= window_start) & (df_dist_10['t (s)'] <= window_end)]
        
        ax.plot(df_zoom['t (s)'], df_zoom['Raw RPM'], color='gray', alpha=0.4, label='Raw RPM', linewidth=1)
        ax.plot(df_zoom['t (s)'], df_zoom['Filtered RPM'], color='#1f77b4', linewidth=2, label='Filtered RPM')
        
        ax.axhline(350, color='red', linestyle='--', label='Target')
        ax.axvline(event_t, color=color, linestyle=style, linewidth=2, label=event_name.replace("_", " "))
        
        event_title = event_name.replace("_", " ")
        if "Drop" in event_title: event_title = "Water " + event_title
        
        ax.set_title(f"{event_title} (t = {event_t}s)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("RPM")
        
        if "Baffle" in event_name:
            ax.set_ylim(280, 400)
        else:
            ax.set_ylim(300, 390)
            
        ax.legend(loc='best')
        ax.grid(True, linestyle=':', alpha=0.7)
        
        filename = f"fig{idx}_10rads_{event_name.lower()}.png"
        plt.savefig(os.path.join(output_dir, filename))
        plt.close(fig)

# ==========================================
# 5. 0.5 rad/s Load Disturbance Overview
# ==========================================
def plot_disturbance_overview_05():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_05['t (s)'], df_05['Filtered RPM'], label='Filtered RPM', color='#1f77b4', alpha=0.9)
    ax.plot(df_05['t (s)'], df_05['Raw RPM'], label='Raw RPM', color='gray', alpha=0.3, linewidth=1)
    ax.axhline(350, color='red', linestyle='--', label='Target (350 RPM)')

    water_drops = [47, 78, 107, 133, 158]
    for drop in water_drops:
        ax.axvline(drop, color='teal', linestyle=':', linewidth=1.5, label='Water Drop' if drop == 47 else "")

    ax.axvline(209, color='orange', linestyle='--', linewidth=1.5, label='Baffles Inserted')
    ax.axvline(235, color='green', linestyle='--', linewidth=1.5, label='Baffles Removed')

    ax.set_title("0.5 rad/s PI Controller: Full Disturbance Response")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("RPM")
    ax.set_xlim(0, 260)
    ax.set_ylim(-20, 420)
    ax.legend(loc='lower left')
    ax.grid(True, linestyle=':', alpha=0.7)
    
    plt.savefig(os.path.join(output_dir, "fig11_05rads_disturbance_overview.png"))
    plt.close(fig)

# ==========================================
# 6. 0.5 rad/s Isolated Event Zooms
# ==========================================
def plot_isolated_events_05():
    events = {
        "Drop_1": (47, "teal", ":"),
        "Drop_2": (78, "teal", ":"),
        "Drop_3": (107, "teal", ":"),
        "Drop_4": (133, "teal", ":"),
        "Drop_5": (158, "teal", ":"),
        "Baffle_Insert": (209, "orange", "--"),
        "Baffle_Remove": (235, "green", "--")
    }

    for idx, (event_name, (event_t, color, style)) in enumerate(events.items(), start=12):
        fig, ax = plt.subplots(figsize=(6, 4))
        
        window_start = event_t - 2
        window_end = event_t + 8
        df_zoom = df_05[(df_05['t (s)'] >= window_start) & (df_05['t (s)'] <= window_end)]
        
        ax.plot(df_zoom['t (s)'], df_zoom['Raw RPM'], color='gray', alpha=0.4, label='Raw RPM', linewidth=1)
        ax.plot(df_zoom['t (s)'], df_zoom['Filtered RPM'], color='#1f77b4', linewidth=2, label='Filtered RPM')
        
        ax.axhline(350, color='red', linestyle='--', label='Target')
        ax.axvline(event_t, color=color, linestyle=style, linewidth=2, label=event_name.replace("_", " "))
        
        event_title = event_name.replace("_", " ")
        if "Drop" in event_title: event_title = "Water " + event_title
        
        ax.set_title(f"{event_title} (t = {event_t}s)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("RPM")
        
        if "Baffle" in event_name:
            ax.set_ylim(280, 400)
        else:
            ax.set_ylim(300, 390)
            
        ax.legend(loc='best')
        ax.grid(True, linestyle=':', alpha=0.7)
        
        filename = f"fig{idx}_05rads_{event_name.lower()}.png"
        plt.savefig(os.path.join(output_dir, filename))
        plt.close(fig)

# ==========================================
# Execute Script
# ==========================================
if __name__ == "__main__":
    print("Generating plots...")
    plot_step_responses()
    plot_disturbance_overview_10()
    plot_isolated_events_10()
    plot_disturbance_overview_05()
    plot_isolated_events_05()
    print("Complete. All thesis-formatted plots saved to directory.")
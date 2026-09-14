from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Data Setup
filename = Path(__file__).resolve().parent / "mixr1_log_20260909_163617_256ppr_20ms_WATERTESTACTUALDATA.csv"
df = pd.read_csv(filename)
target_rpm = 460
output_dir = Path(__file__).resolve().parent / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

# Style settings for thesis-level quality
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'legend.fontsize': 12,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'lines.linewidth': 2
})

color_target = '#d62728'
color_actual = '#004c99'
color_disturb = '#ff7f0e'

pours = [
    {"time": 34.0,  "label": "Pour 1"},
    {"time": 65.0,  "label": "Pour 2"},
    {"time": 95.0,  "label": "Pour 3"},
    {"time": 123.5, "label": "Pour 4"}
]

# --- 1. OVERVIEW GRAPH ---
fig, ax = plt.subplots(figsize=(14, 6))
plot_df = df[(df['t (s)'] >= 0) & (df['t (s)'] <= 150)]

ax.axhline(target_rpm, color=color_target, linestyle='--', linewidth=2, label=f'Target Command ({target_rpm} RPM)')
ax.plot(plot_df['t (s)'], plot_df['Filtered RPM'], color=color_actual, label='System Response (Filtered RPM)')

for i, p in enumerate(pours):
    ax.axvspan(p['time'], p['time']+5, color=color_disturb, alpha=0.2, label='Disturbance Injection' if i == 0 else "")
    ax.axvline(p['time'], color=color_disturb, linestyle=':', linewidth=2)
    ax.text(p['time'] - 2, 510, p['label'], color='#8c564b', fontweight='bold', fontsize=12, rotation=90)

ax.set_title('Global System Response: Step Load Disturbances (0 - 150s)', fontweight='bold', pad=15)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Motor Speed (RPM)')
ax.set_xlim(0, 150)
ax.set_ylim(400, 520)
ax.legend(loc='lower right', frameon=True, fancybox=True, shadow=True)
plt.tight_layout()
fig.savefig(output_dir / 'thesis_overview.png', dpi=300)
plt.close(fig)

# --- 2. ZOOMED GRAPHS ---
def generate_zoomed_plot(center_t, title, save_name):
    fig, ax = plt.subplots(figsize=(10, 5))
    t_start = center_t - 10
    t_end = center_t + 20
    
    zoom_df = df[(df['t (s)'] >= t_start) & (df['t (s)'] <= t_end)]
    
    ax.axhline(target_rpm, color=color_target, linestyle='--', linewidth=2, label=f'Target Command ({target_rpm} RPM)')
    ax.plot(zoom_df['t (s)'], zoom_df['Filtered RPM'], color=color_actual, label='System Response')
    
    ax.axvspan(center_t, center_t+5, color=color_disturb, alpha=0.2, label='Load Injection (Approx. Settling)')
    ax.axvline(center_t, color=color_disturb, linestyle=':', linewidth=2)
    
    dip_window = zoom_df[(zoom_df['t (s)'] >= center_t) & (zoom_df['t (s)'] <= center_t + 5)]
    if not dip_window.empty:
        min_rpm = dip_window['Filtered RPM'].min()
        min_t = dip_window.loc[dip_window['Filtered RPM'].idxmin(), 't (s)']
        ax.plot(min_t, min_rpm, 'ro', markersize=8)
        ax.annotate(f'Peak Dip: {min_rpm:.1f} RPM', 
                    xy=(min_t, min_rpm), xytext=(min_t + 1, min_rpm - 10),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6),
                    fontsize=11, fontweight='bold')
    
    ax.set_title(title, fontweight='bold', pad=15)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Motor Speed (RPM)')
    ax.set_xlim(t_start, t_end)
    ax.set_ylim(420, 500)
    ax.legend(loc='lower right', frameon=True, shadow=True)
    
    plt.tight_layout()
    fig.savefig(save_name, dpi=300)
    plt.close(fig)

generate_zoomed_plot(34.0, 'Transient Response: Disturbance 1 (~34s)', output_dir / 'thesis_zoom_1.png')
generate_zoomed_plot(65.0, 'Transient Response: Disturbance 2 (~65s)', output_dir / 'thesis_zoom_2.png')
generate_zoomed_plot(95.0, 'Transient Response: Disturbance 3 (~95s)', output_dir / 'thesis_zoom_3.png')
generate_zoomed_plot(123.5, 'Transient Response: Disturbance 4 (~123.5s)', output_dir / 'thesis_zoom_4.png')
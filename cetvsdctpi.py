import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import matplotlib as mpl

# --- POWERPOINT PRESENTATION STYLING ---
mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 16,
    'axes.labelsize': 18,
    'axes.titlesize': 22,
    'legend.fontsize': 14,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'lines.linewidth': 2.5,
    'axes.grid': True,
    'grid.alpha': 0.5,
    'grid.linestyle': '--',
    'figure.dpi': 150,
    'figure.autolayout': True 
})

# --- CONFIGURATION ---
FILE_DCT = 'dct_1500rpm.csv'
FILE_CET = 'cet_1500rpm.csv'

try:
    df_dct = pd.read_csv(FILE_DCT)
    df_cet = pd.read_csv(FILE_CET)
except FileNotFoundError:
    print(f"CRITICAL ERROR: Place '{FILE_DCT}' and '{FILE_CET}' in the same folder as this script.")
    sys.exit(1)

t_dct = 'elapsed_s' if 'elapsed_s' in df_dct.columns else 't (s)'
t_cet = 'elapsed_s' if 'elapsed_s' in df_cet.columns else 't (s)'
rpm_dct = 'raw_rpm' if 'raw_rpm' in df_dct.columns else 'Raw RPM'
rpm_cet = 'raw_rpm' if 'raw_rpm' in df_cet.columns else 'Raw RPM'
target_col = 'target_rpm'
step_col = 'step_index' if 'step_index' in df_dct.columns else 'Step'

stats = []
steps = sorted(list(set(df_dct[step_col].unique()).intersection(set(df_cet[step_col].unique()))))

for step in steps:
    dct_step = df_dct[df_dct[step_col] == step]
    cet_step = df_cet[df_cet[step_col] == step]
    
    dct_stable = dct_step[dct_step[t_dct] > (dct_step[t_dct].min() + 4)]
    cet_stable = cet_step[cet_step[t_cet] > (cet_step[t_cet].min() + 4)]
    
    if len(dct_stable) > 0 and len(cet_stable) > 0:
        target_val = dct_step[target_col].iloc[0]
        if target_val <= 0: continue
        
        stats.append({
            'Target RPM': target_val,
            'DCT Mean Error': np.abs(dct_stable[target_col] - dct_stable[rpm_dct]).mean(),
            'CET Mean Error': np.abs(cet_stable[target_col] - cet_stable[rpm_cet]).mean(),
            'DCT Error SD': (dct_stable[target_col] - dct_stable[rpm_dct]).std(),
            'CET Error SD': (cet_stable[target_col] - cet_stable[rpm_cet]).std()
        })

stats_df = pd.DataFrame(stats)

# ==========================================
# FIGURE 1: Full PI Sweep Tracking
# ==========================================
fig1 = plt.figure(figsize=(12, 6.75)) 

plt.plot(df_dct[t_dct], df_dct[rpm_dct], color='#d95f02', alpha=0.7, label='DCT Measured Velocity')
plt.plot(df_cet[t_cet], df_cet[rpm_cet], color='#1b9e77', alpha=0.9, label='CET Measured Velocity')
plt.plot(df_cet[t_cet], df_cet[target_col], color='black', linestyle=':', linewidth=3.0, label='Target Setpoint')

plt.title('Closed-Loop Tracking Performance Comparison', fontweight='bold')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (RPM)')
plt.legend(loc='upper left', frameon=True, edgecolor='black')
plt.savefig('ppt_pi_full_sweep.png', bbox_inches='tight')

# ==========================================
# FIGURE 2: Steady-State Oscillation
# ==========================================
fig2 = plt.figure(figsize=(12, 6.75))

target_step = steps[-1] if len(steps) > 0 else steps[0]
zoom_start = df_dct[df_dct[step_col] == target_step][t_dct].min() + 2
zoom_end = zoom_start + 10 

df_dct_zoom = df_dct[(df_dct[t_dct] > zoom_start) & (df_dct[t_dct] < zoom_end)]
df_cet_zoom = df_cet[(df_cet[t_cet] > zoom_start) & (df_cet[t_cet] < zoom_end)]
target_val = df_cet_zoom[target_col].iloc[0]

# Applied drawstyle='steps-post' to both plots for accurate comparison of digital control loops
plt.plot(df_dct_zoom[t_dct], df_dct_zoom[rpm_dct], color='#d95f02', alpha=0.9, drawstyle='steps-post', label='DCT Control Response')
plt.plot(df_cet_zoom[t_cet], df_cet_zoom[rpm_cet], color='#1b9e77', drawstyle='steps-post', label='CET Control Response')
plt.axhline(target_val, color='black', linestyle=':', linewidth=3.0, label=f'Target ({target_val:.0f} RPM)')

plt.title(f'Steady-State PI Actuation at {target_val:.0f} RPM', fontweight='bold')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (RPM)')
plt.legend(loc='upper right', frameon=True, edgecolor='black')

y_min = min(df_dct_zoom[rpm_dct].min(), df_cet_zoom[rpm_cet].min())
y_max = max(df_dct_zoom[rpm_dct].max(), df_cet_zoom[rpm_cet].max())
y_range = y_max - y_min
if y_range > 0:
    plt.ylim(y_min - 0.2 * y_range, y_max + 0.2 * y_range)

plt.savefig('ppt_pi_steady_state.png', bbox_inches='tight')

# ==========================================
# FIGURE 3: Error Standard Deviation Bar Chart
# ==========================================
fig3 = plt.figure(figsize=(12, 6.75))
bar_width = 0.35
index = np.arange(len(stats_df))

plt.bar(index, stats_df['DCT Error SD'], bar_width, label=r'DCT $\sigma_{error}$', color='#d95f02', edgecolor='black', linewidth=1.5)
plt.bar(index + bar_width, stats_df['CET Error SD'], bar_width, label=r'CET $\sigma_{error}$', color='#1b9e77', edgecolor='black', linewidth=1.5)
plt.xlabel('Target Velocity Setpoint (RPM)')
plt.ylabel('Tracking Error StDev (RPM)')
plt.title('Control Loop Precision Variance Analysis', fontweight='bold')
plt.xticks(index + bar_width / 2, stats_df['Target RPM'].astype(int).astype(str).tolist())
plt.legend(frameon=True, edgecolor='black')
plt.savefig('ppt_pi_error_barchart.png', bbox_inches='tight')
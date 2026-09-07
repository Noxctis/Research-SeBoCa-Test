import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURATION ---
FILE_DCT = 'dct_1500rpm.csv'
FILE_CET = 'cet_1500rpm.csv'

try:
    df_dct = pd.read_csv(FILE_DCT)
    df_cet = pd.read_csv(FILE_CET)
    
    # Standardize column names
    t_dct = 'elapsed_s' if 'elapsed_s' in df_dct.columns else 't (s)'
    t_cet = 'elapsed_s' if 'elapsed_s' in df_cet.columns else 't (s)'
    rpm_dct = 'raw_rpm' if 'raw_rpm' in df_dct.columns else 'Raw RPM'
    rpm_cet = 'raw_rpm' if 'raw_rpm' in df_cet.columns else 'Raw RPM'
    target_col = 'target_rpm'
    step_col = 'step_index'
    
    # Calculate Error Metrics per Step
    stats = []
    steps = sorted(list(set(df_dct[step_col].unique()).intersection(set(df_cet[step_col].unique()))))
    
    for step in steps:
        dct_step = df_dct[df_dct[step_col] == step]
        cet_step = df_cet[df_cet[step_col] == step]
        
        # Drop the first 3 seconds of the step to ignore the initial PID windup/overshoot
        dct_stable = dct_step[dct_step[t_dct] > (dct_step[t_dct].min() + 3)]
        cet_stable = cet_step[cet_step[t_cet] > (cet_step[t_cet].min() + 3)]
        
        if len(dct_stable) > 0 and len(cet_stable) > 0:
            target_val = dct_step[target_col].iloc[0]
            if target_val <= 0: continue # Skip 0 RPM target
            
            stats.append({
                'Target RPM': target_val,
                'DCT Mean Error': np.abs(dct_stable[target_col] - dct_stable[rpm_dct]).mean(),
                'CET Mean Error': np.abs(cet_stable[target_col] - cet_stable[rpm_cet]).mean(),
                'DCT Error SD': (dct_stable[target_col] - dct_stable[rpm_dct]).std(),
                'CET Error SD': (cet_stable[target_col] - cet_stable[rpm_cet]).std()
            })
            
    stats_df = pd.DataFrame(stats)
    
    # --- Plot 1: Full PI Sweep Tracking ---
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(14, 7))
    
    plt.plot(df_dct[t_dct], df_dct[rpm_dct], color='#ff7f00', alpha=0.7, label='DCT + PI (Measured Velocity)')
    plt.plot(df_cet[t_cet], df_cet[rpm_cet], color='#377eb8', alpha=0.9, label='CET + PI (Measured Velocity)')
    plt.plot(df_cet[t_cet], df_cet[target_col], color='black', linestyle='--', linewidth=2, label='Target RPM (Setpoint)')
    
    plt.title('Closed-Loop PI Control Tracking: CET vs DCT', fontweight='bold', fontsize=16)
    plt.xlabel('Time (s)', fontsize=14)
    plt.ylabel('Velocity (RPM)', fontsize=14)
    plt.legend(loc='upper left', fontsize=12)
    plt.tight_layout()
    plt.savefig('pi_full_sweep_comparison.png')
    print("Saved: pi_full_sweep_comparison.png")
    
    # --- Plot 2: Zoomed Steady-State (Find a step around 1000-1500 RPM) ---
    plt.figure(figsize=(12, 6))
    
    # Find a mid/high-speed step (e.g., Step 6)
    target_step = 6 if 6 in steps else steps[-1]
    zoom_start = df_dct[df_dct[step_col] == target_step][t_dct].min() + 5
    zoom_end = zoom_start + 5
    
    df_dct_zoom = df_dct[(df_dct[t_dct] > zoom_start) & (df_dct[t_dct] < zoom_end)]
    df_cet_zoom = df_cet[(df_cet[t_cet] > zoom_start) & (df_cet[t_cet] < zoom_end)]
    target_val = df_cet_zoom[target_col].iloc[0]
    
    plt.plot(df_dct_zoom[t_dct], df_dct_zoom[rpm_dct], color='#ff7f00', alpha=0.9, drawstyle='steps-post', label='DCT PI Output (Hunting/Oscillating)')
    plt.plot(df_cet_zoom[t_cet], df_cet_zoom[rpm_cet], color='#377eb8', linewidth=2, label='CET PI Output (Stable Lock)')
    plt.axhline(target_val, color='black', linestyle='--', linewidth=2, label=f'Target Setpoint ({target_val} RPM)')
    
    plt.title(f'PI Controller Steady-State Lock (Target = {target_val} RPM)', fontweight='bold', fontsize=16)
    plt.xlabel('Time (s)', fontsize=14)
    plt.ylabel('Velocity (RPM)', fontsize=14)
    plt.legend(loc='upper right', fontsize=12)
    
    plt.ylim(target_val - 25, target_val + 25)
    plt.tight_layout()
    plt.savefig('pi_zoomed_steady_state.png')
    print("Saved: pi_zoomed_steady_state.png")
    
    # --- Output Statistics ---
    print("\n--- PI CONTROLLER TRACKING ERROR ---")
    print(stats_df.to_markdown(index=False, floatfmt=".2f"))

except FileNotFoundError:
    print(f"ERROR: Cannot find '{FILE_DCT}' or '{FILE_CET}'.")
except Exception as e:
    print(f"Error: {e}")
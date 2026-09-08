import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Change these filenames to match your local CSV files
FILE_DCT = 'dct_pwm_sweep.csv'
FILE_CET = 'cet_pwm_sweep.csv'

try:
    df_dct = pd.read_csv(FILE_DCT)
    df_cet = pd.read_csv(FILE_CET)
    
    # Standardize column names
    t_dct = 'elapsed_s' if 'elapsed_s' in df_dct.columns else 't (s)'
    t_cet = 'elapsed_s' if 'elapsed_s' in df_cet.columns else 't (s)'
    rpm_dct = 'raw_rpm' if 'raw_rpm' in df_dct.columns else 'Raw RPM'
    rpm_cet = 'raw_rpm' if 'raw_rpm' in df_cet.columns else 'Raw RPM'
    step_col = 'step_index' if 'step_index' in df_dct.columns else 'Step'
    pwm_col = 'pwm_percent' if 'pwm_percent' in df_dct.columns else 'PWM'
    
    stats = []
    # Intersect steps to ensure we only compare matching data
    steps = sorted(list(set(df_dct[step_col].unique()).intersection(set(df_cet[step_col].unique()))))
    
    for step in steps:
        dct_step = df_dct[df_dct[step_col] == step]
        cet_step = df_cet[df_cet[step_col] == step]
        
        # Exclude the first 2 seconds of the step to capture steady-state only
        dct_stable = dct_step[dct_step[t_dct] > (dct_step[t_dct].min() + 2)]
        cet_stable = cet_step[cet_step[t_cet] > (cet_step[t_cet].min() + 2)]
        
        if len(dct_stable) > 0 and len(cet_stable) > 0:
            pwm_val = dct_step[pwm_col].iloc[0]
            stats.append({
                'Step Index': step,
                'PWM %': pwm_val,
                'DCT Mean RPM': dct_stable[rpm_dct].mean(),
                'CET Mean RPM': cet_stable[rpm_cet].mean(),
                'DCT SD (RPM)': dct_stable[rpm_dct].std(),
                'CET SD (RPM)': cet_stable[rpm_cet].std()
            })
            
    stats_df = pd.DataFrame(stats)
    
    # --- Plot 1: Direct Overlay of Both Methods ---
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(14, 7))
    
    plt.plot(df_dct[t_dct], df_dct[rpm_dct], color='#ff7f00', alpha=0.8, drawstyle='steps-post', label='Discrete Time (DCT) Velocity')
    plt.plot(df_cet[t_cet], df_cet[rpm_cet], color='#377eb8', alpha=0.9, linewidth=1.5, label='Synchronous CET (Mod-4) Velocity')
    
    plt.title('Open-Loop PWM Sweep: Kinematics Algorithm Direct Overlay', fontweight='bold', fontsize=16)
    plt.xlabel('Time (s)', fontsize=14)
    plt.ylabel('Measured Velocity (RPM)', fontsize=14)
    plt.legend(loc='upper left', fontsize=12)
    plt.tight_layout()
    plt.savefig('overlay_pwm_sweep.png')
    print("Saved: overlay_pwm_sweep.png")
    
    # --- Plot 2: Zoomed Overlay (50% PWM Steady-State) ---
    plt.figure(figsize=(12, 6))
    
    zoom_start = df_dct[df_dct[step_col] == 5][t_dct].min() + 5
    zoom_end = zoom_start + 5
    
    df_dct_zoom = df_dct[(df_dct[t_dct] > zoom_start) & (df_dct[t_dct] < zoom_end)]
    df_cet_zoom = df_cet[(df_cet[t_cet] > zoom_start) & (df_cet[t_cet] < zoom_end)]
    
    plt.plot(df_dct_zoom[t_dct], df_dct_zoom[rpm_dct], color='#ff7f00', alpha=0.9, drawstyle='steps-post', label='DCT Velocity (High Quantization Noise)')
    plt.plot(df_cet_zoom[t_cet], df_cet_zoom[rpm_cet], color='#377eb8', linewidth=2, label='CET Velocity (Hardware Determinism)')
    
    plt.title('Zoomed Direct Overlay (50% PWM Steady-State)', fontweight='bold', fontsize=16)
    plt.xlabel('Time (s)', fontsize=14)
    plt.ylabel('Velocity (RPM)', fontsize=14)
    plt.legend(loc='upper right', fontsize=12)
    
    y_mean = df_cet_zoom[rpm_cet].mean()
    plt.ylim(y_mean - 10, y_mean + 10)
    plt.tight_layout()
    plt.savefig('zoomed_overlay_pwm_sweep.png')
    print("Saved: zoomed_overlay_pwm_sweep.png")
    
    # --- Plot 3: Noise Comparison Bar Chart ---
    plt.figure(figsize=(12, 6))
    bar_width = 0.35
    index = np.arange(len(stats_df))
    
    plt.bar(index, stats_df['DCT SD (RPM)'], bar_width, label='DCT Noise (SD)', color='#ff7f00')
    plt.bar(index + bar_width, stats_df['CET SD (RPM)'], bar_width, label='CET Noise (SD)', color='#377eb8')
    
    plt.xlabel('PWM Duty Cycle (%)', fontsize=14)
    plt.ylabel('Standard Deviation (RPM)', fontsize=14)
    plt.title('Quantization Noise Magnitude per Voltage Step', fontweight='bold', fontsize=16)
    plt.xticks(index + bar_width / 2, stats_df['PWM %'].astype(str).tolist())
    plt.legend(fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('noise_bar_chart.png')
    print("Saved: noise_bar_chart.png\n")
    
    # Print markdown table data
    print("--- STEADY-STATE STATISTICAL TABLE ---")
    print(stats_df.to_markdown(index=False, floatfmt=".2f"))

except FileNotFoundError:
    print(f"ERROR: Cannot find '{FILE_DCT}' or '{FILE_CET}'. Verify the filenames match your directory.")
except Exception as e:
    print(f"Error: {e}")
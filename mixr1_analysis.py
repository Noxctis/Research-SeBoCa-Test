import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# CONFIGURATION
# ==========================================
TARGET_SETPOINT_RPM = 1500.0  
SETTLING_BAND = 0.02          

def analyze_log(filepath: str):
    print(f"\n{'='*50}\nAnalyzing: {os.path.basename(filepath)}\n{'='*50}")
    
    # Load Data and sanitize headers
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()
    
    # Legacy CSV compatibility mapping
    col_t = 't (s)' if 't (s)' in df.columns else 'time_s'
    col_raw = 'Raw RPM' if 'Raw RPM' in df.columns else 'Raw_RPM'
    col_filt = 'Filtered RPM' if 'Filtered RPM' in df.columns else 'Filtered_RPM'
    
    t = df[col_t].values
    raw_rpm = df[col_raw].values
    filt_rpm = df[col_filt].values
    
    # 1. OS Determinism (Jitter)
    delta_t = np.diff(t)
    mean_dt = np.mean(delta_t)
    max_jitter = np.max(np.abs(delta_t - mean_dt))
    print(f"[SYSTEM] Mean Loop Time : {mean_dt*1000:.2f} ms ({1/mean_dt:.1f} Hz)")
    print(f"[SYSTEM] Max OS Jitter  : {max_jitter*1000:.2f} ms")
    
    # 2. Steady-State Noise 
    settled_idx = int(len(raw_rpm) * 0.8)
    steady_raw = raw_rpm[settled_idx:]
    steady_filt = filt_rpm[settled_idx:]
    
    sigma_raw = np.std(steady_raw)
    sigma_filt = np.std(steady_filt)
    steady_state_val = np.mean(steady_filt)
    ss_error = steady_state_val - TARGET_SETPOINT_RPM
    
    print(f"\n[NOISE] Raw Std Dev     : ±{sigma_raw:.2f} RPM")
    print(f"[NOISE] Filtered Std Dev: ±{sigma_filt:.2f} RPM")
    print(f"[ERROR] Steady-State Err: {ss_error:.2f} RPM")
    
    # 3. Step Response Metrics 
    max_rpm = np.max(filt_rpm)
    overshoot_pct = ((max_rpm - steady_state_val) / steady_state_val) * 100 if steady_state_val > 0 else 0
    print(f"\n[STEP]  Max Overshoot   : {overshoot_pct:.2f}% ({max_rpm:.1f} RPM)")
    
    ten_pct = 0.10 * steady_state_val
    ninety_pct = 0.90 * steady_state_val
    
    t_10 = t[np.argmax(filt_rpm >= ten_pct)] if np.any(filt_rpm >= ten_pct) else 0
    t_90 = t[np.argmax(filt_rpm >= ninety_pct)] if np.any(filt_rpm >= ninety_pct) else 0
    rise_time = t_90 - t_10 if (t_90 > 0 and t_10 > 0) else float('nan')
    print(f"[STEP]  Rise Time (Tr)  : {rise_time:.3f} s")
    
    upper_band = steady_state_val * (1 + SETTLING_BAND)
    lower_band = steady_state_val * (1 - SETTLING_BAND)
    
    out_of_band = np.where((filt_rpm < lower_band) | (filt_rpm > upper_band))[0]
    if len(out_of_band) > 0 and out_of_band[-1] < len(t) - 1:
        settling_time = t[out_of_band[-1] + 1] - t[0]
        print(f"[STEP]  Settling Time   : {settling_time:.3f} s")
    else:
        print("[STEP]  Settling Time   : Did not settle")

    # ==========================================
    # RESEARCH-GRADE PLOTTING
    # ==========================================
    plt.style.use('seaborn-v0_8-paper')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), dpi=150, gridspec_kw={'height_ratios': [3, 1]})
    
    ax1.plot(t, raw_rpm, color='gray', alpha=0.4, linewidth=1, label='Raw Hardware RPM')
    ax1.plot(t, filt_rpm, color='#1f77b4', linewidth=2, label='Filtered RPM (EMA)')
    ax1.axhline(TARGET_SETPOINT_RPM, color='red', linestyle='--', linewidth=1.5, label='Target Setpoint')
    
    ax1.axhspan(TARGET_SETPOINT_RPM * (1 - SETTLING_BAND), 
                TARGET_SETPOINT_RPM * (1 + SETTLING_BAND), 
                color='green', alpha=0.1, label='±2% Settling Band')

    # FIX: Applying raw strings ('r' and 'rf') to prevent LaTeX escape sequence errors
    ax1.set_title(rf"MIXR-1 Step Response Analysis\n($t_r$={rise_time:.2f}s, OS={overshoot_pct:.1f}%, $\sigma$={sigma_filt:.1f} RPM)", fontweight='bold')
    ax1.set_ylabel('Velocity (RPM)', fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.7)
    ax1.legend(loc='lower right')
    
    ax2.plot(t[1:], delta_t * 1000, color='#d62728', marker='.', linestyle='none', markersize=3)
    ax2.axhline(mean_dt * 1000, color='black', linewidth=1)
    
    # FIX: Applying raw strings to LaTeX axis labels
    ax2.set_title(r"Operating System Jitter ($\Delta t$ Variance)", fontweight='bold')
    ax2.set_xlabel('Time (s)', fontweight='bold')
    ax2.set_ylabel(r'Loop $\Delta t$ (ms)', fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.7)
    
    plt.tight_layout()
    plot_filename = filepath.replace('.csv', '_analysis.png')
    plt.savefig(plot_filename)
    print(f"\n[FILE]  Saved characterization plot to: {plot_filename}")
    plt.show()

if __name__ == "__main__":
    target_file = "mixr1_log_20260714_164644.csv"
    if os.path.exists(target_file):
        analyze_log(target_file)
    else:
        print(f"File not found: {target_file}")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
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
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

date_str = datetime.now().strftime("%Y%m%d")
output_dir = f"MIXR1_PI_ClosedLoop_Bode_{date_str}"
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory created: {output_dir}/")

# ==========================================
# 2. Curve Fitting Core Math
# ==========================================
def sine_func(t, A, omega, phi, offset):
    return A * np.sin(omega * t + phi) + offset

def extract_tracking_dynamics(t, target, rpm, freq):
    """Performs non-linear least squares fit to extract closed-loop tracking parameters."""
    omega_guess = 2.0 * np.pi * freq
    
    # 1. Fit Target RPM (The Input Command)
    p0_target = [(target.max() - target.min()) / 2.0, omega_guess, 0.0, target.mean()]
    popt_target, _ = curve_fit(sine_func, t, target, p0=p0_target)
    
    # 2. Fit Actual RPM (The Controller's Output)
    p0_rpm = [(rpm.max() - rpm.min()) / 2.0, omega_guess, 0.0, rpm.mean()]
    popt_rpm, _ = curve_fit(sine_func, t, rpm, p0=p0_rpm)
    
    # 3. Phase Calculations
    phase_target = popt_target[2] % (2 * np.pi)
    phase_rpm = popt_rpm[2] % (2 * np.pi)
    
    # Correct for negative amplitudes flipping the phase by 180 degrees
    if popt_target[0] < 0:
        phase_target += np.pi
        popt_target[0] = abs(popt_target[0])
    if popt_rpm[0] < 0:
        phase_rpm += np.pi
        popt_rpm[0] = abs(popt_rpm[0])
        
    phase_diff_rad = (phase_rpm - phase_target)
    phase_diff_rad = (phase_diff_rad + np.pi) % (2 * np.pi) - np.pi
    
    # Tracking Gain: 1.0 means perfect tracking. < 1.0 means attenuation.
    tracking_gain = popt_rpm[0] / popt_target[0]
    phase_shift_deg = np.degrees(phase_diff_rad)
    
    return popt_rpm, tracking_gain, phase_shift_deg

# ==========================================
# 3. Data Processing & Plotting
# ==========================================
def analyze_closed_loop_bode():
    # Map your exact filenames
    files_map = {
        0.1: {'load': 'sine_0_1Hz Load 2.csv', 'noload': 'sine_0_1Hz no load 2.csv'},
        0.5: {'load': 'sine_0_5Hz Load 2.csv', 'noload': 'sine_0_5Hz no load 2.csv'},
        1.0: {'load': 'sine_1_0Hz Load 2.csv', 'noload': 'sine_1_0Hz no load 2.csv'}
    }
    
    fig_comb, axes_comb = plt.subplots(3, 1, figsize=(10, 14), sharex=False)
    fig_comb.subplots_adjust(hspace=0.4)
    
    fig_nl, axes_nl = plt.subplots(3, 1, figsize=(10, 14), sharex=False)
    fig_nl.subplots_adjust(hspace=0.4)

    fig_l, axes_l = plt.subplots(3, 1, figsize=(10, 14), sharex=False)
    fig_l.subplots_adjust(hspace=0.4)
    
    text_box_props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray')

    for i, (freq, fnames) in enumerate(files_map.items()):
        load_file = fnames['load']
        noload_file = fnames['noload']
        
        ax_c = axes_comb[i]
        ax_nl = axes_nl[i]
        ax_l = axes_l[i]
        
        # Secondary Y-axes for PWM Control Effort
        ax2_c = ax_c.twinx()
        ax2_nl = ax_nl.twinx()
        ax2_l = ax_l.twinx()
        
        print(f"\n--- {freq} Hz PI Closed-Loop Analysis ---")
        
        text_str_comb = ""
        
        # =====================================
        # --- NO-LOAD ANALYSIS ---
        # =====================================
        if os.path.exists(noload_file):
            df_nl = pd.read_csv(noload_file)
            df_nl_steady = df_nl[df_nl['elapsed_s'] > 5.0]
            
            t_nl = df_nl_steady['elapsed_s'].to_numpy()
            target_nl = df_nl_steady['target_rpm'].to_numpy()
            rpm_nl = df_nl_steady['filtered_rpm'].to_numpy()
            
            fit_nl, gain_nl, phase_nl = extract_tracking_dynamics(t_nl, target_nl, rpm_nl, freq)
            
            print(f"NO-LOAD | Tracking Ratio: {gain_nl:.3f} | Phase Lag: {phase_nl:.1f}°")
            
            # --- Plot No-Load Combined ---
            ax_c.plot(df_nl['elapsed_s'], df_nl['filtered_rpm'], color='#2ca02c', label='No-Load RPM', alpha=0.5)
            ax_c.plot(t_nl, sine_func(t_nl, *fit_nl), color='#155d15', linestyle='--', linewidth=1.5, label='No-Load Fit')
            text_str_comb += f"No-Load: Tracking={gain_nl:.3f}, Lag={phase_nl:.1f}°\n"
            
            # --- Plot No-Load Individual ---
            ax_nl.plot(df_nl['elapsed_s'], df_nl['target_rpm'], color='#d62728', alpha=0.8, linestyle='--', label='Target RPM')
            ax_nl.plot(df_nl['elapsed_s'], df_nl['filtered_rpm'], color='#2ca02c', label='Actual RPM', alpha=0.9)
            ax_nl.plot(t_nl, sine_func(t_nl, *fit_nl), color='k', linestyle=':', linewidth=2, label='Actual RPM Fit')
            ax2_nl.plot(df_nl['elapsed_s'], df_nl['pwm'], color='#1f77b4', alpha=0.3, label='PWM Control Effort')
            
            text_str_nl = f"Tracking Ratio: {gain_nl:.3f}\nPhase Lag: {phase_nl:.1f}°"
            ax_nl.text(0.02, 0.05, text_str_nl, transform=ax_nl.transAxes, fontsize=10, verticalalignment='bottom', bbox=text_box_props)
            
            ax_nl.set_title(f"{freq} Hz PI Tracking (No-Load)")
            ax_nl.set_ylabel("RPM")
            ax2_nl.set_ylabel("PWM (Effort)")
            ax_nl.grid(True, linestyle=':', alpha=0.7)
            
            lines, labels = ax_nl.get_legend_handles_labels()
            lines2, labels2 = ax2_nl.get_legend_handles_labels()
            ax2_nl.legend(lines + lines2, labels + labels2, loc='upper right')
        else:
            print(f"WARNING: No-Load file not found: {noload_file}")

        # =====================================
        # --- LOADED ANALYSIS ---
        # =====================================
        if os.path.exists(load_file):
            df_l = pd.read_csv(load_file)
            df_l_steady = df_l[df_l['elapsed_s'] > 5.0]
            
            t_l = df_l_steady['elapsed_s'].to_numpy()
            target_l = df_l_steady['target_rpm'].to_numpy()
            rpm_l = df_l_steady['filtered_rpm'].to_numpy()
            
            fit_l, gain_l, phase_l = extract_tracking_dynamics(t_l, target_l, rpm_l, freq)
            
            print(f"LOADED  | Tracking Ratio: {gain_l:.3f} | Phase Lag: {phase_l:.1f}°")
            
            # --- Plot Loaded Combined ---
            ax_c.plot(df_l['elapsed_s'], df_l['target_rpm'], color='#d62728', alpha=0.8, linestyle='--', label='Target RPM')
            ax_c.plot(df_l['elapsed_s'], df_l['filtered_rpm'], color='#ff7f0e', label='Loaded RPM', alpha=0.8)
            ax_c.plot(t_l, sine_func(t_l, *fit_l), color='#8c4304', linestyle='-.', linewidth=2, label='Loaded Fit')
            text_str_comb += f"Loaded: Tracking={gain_l:.3f}, Lag={phase_l:.1f}°"
            
            # --- Plot Loaded Individual ---
            ax_l.plot(df_l['elapsed_s'], df_l['target_rpm'], color='#d62728', alpha=0.8, linestyle='--', label='Target RPM')
            ax_l.plot(df_l['elapsed_s'], df_l['filtered_rpm'], color='#ff7f0e', label='Actual RPM', alpha=0.9)
            ax_l.plot(t_l, sine_func(t_l, *fit_l), color='k', linestyle=':', linewidth=2, label='Actual RPM Fit')
            ax2_l.plot(df_l['elapsed_s'], df_l['pwm'], color='#1f77b4', alpha=0.3, label='PWM Control Effort')
            
            text_str_l = f"Tracking Ratio: {gain_l:.3f}\nPhase Lag: {phase_l:.1f}°"
            ax_l.text(0.02, 0.05, text_str_l, transform=ax_l.transAxes, fontsize=10, verticalalignment='bottom', bbox=text_box_props)
            
            ax_l.set_title(f"{freq} Hz PI Tracking (Loaded Tank)")
            ax_l.set_ylabel("RPM")
            ax2_l.set_ylabel("PWM (Effort)")
            ax_l.grid(True, linestyle=':', alpha=0.7)
            
            lines, labels = ax_l.get_legend_handles_labels()
            lines2, labels2 = ax2_l.get_legend_handles_labels()
            ax2_l.legend(lines + lines2, labels + labels2, loc='upper right')
        else:
            print(f"ERROR: Loaded file not found: {load_file}")
            
        # =====================================
        # --- COMBINED GRAPH FORMATTING ---
        # =====================================
        if text_str_comb:
            ax_c.text(0.02, 0.05, text_str_comb.strip(), transform=ax_c.transAxes, fontsize=10, verticalalignment='bottom', bbox=text_box_props)
            
        ax_c.set_title(f"{freq} Hz PI Tracking (Load vs No-Load)")
        ax_c.set_ylabel("RPM")
        ax_c.grid(True, linestyle=':', alpha=0.7)
        
        # Deduplicate legend on combined plot
        handles, labels = ax_c.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax_c.legend(by_label.values(), by_label.keys(), loc='upper right')

    axes_comb[-1].set_xlabel("Time (s)")
    axes_nl[-1].set_xlabel("Time (s)")
    axes_l[-1].set_xlabel("Time (s)")
    
    out_comb = os.path.join(output_dir, "fig1_pi_bode_combined.png")
    out_nl = os.path.join(output_dir, "fig2_pi_bode_noload.png")
    out_l = os.path.join(output_dir, "fig3_pi_bode_loaded.png")
    
    fig_comb.savefig(out_comb)
    fig_nl.savefig(out_nl)
    fig_l.savefig(out_l)
    
    print(f"\nPlots saved to {output_dir}/:")
    print(f" - fig1_pi_bode_combined.png")
    print(f" - fig2_pi_bode_noload.png")
    print(f" - fig3_pi_bode_loaded.png")

if __name__ == "__main__":
    analyze_closed_loop_bode()
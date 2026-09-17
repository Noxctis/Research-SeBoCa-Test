import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os
import glob
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
output_dir = f"MIXR1_Bode_Plots_{date_str}"
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory created: {output_dir}/")

# ==========================================
# 2. Curve Fitting Core Math
# ==========================================
def sine_func(t, A, omega, phi, offset):
    return A * np.sin(omega * t + phi) + offset

def extract_system_dynamics(t, pwm, rpm, freq):
    """Performs non-linear least squares fit to extract plant parameters."""
    omega_guess = 2.0 * np.pi * freq
    
    # Fit PWM
    p0_pwm = [409.0, omega_guess, 0.0, 819.0]
    popt_pwm, _ = curve_fit(sine_func, t, pwm, p0=p0_pwm)
    
    # Fit RPM
    p0_rpm = [(rpm.max() - rpm.min()) / 2.0, omega_guess, 0.0, rpm.mean()]
    popt_rpm, _ = curve_fit(sine_func, t, rpm, p0=p0_rpm)
    
    # Phase Calculations
    phase_pwm = popt_pwm[2] % (2 * np.pi)
    phase_rpm = popt_rpm[2] % (2 * np.pi)
    
    # Correct for negative amplitudes flipping the phase by 180 degrees
    if popt_pwm[0] < 0:
        phase_pwm += np.pi
        popt_pwm[0] = abs(popt_pwm[0])
    if popt_rpm[0] < 0:
        phase_rpm += np.pi
        popt_rpm[0] = abs(popt_rpm[0])
        
    phase_diff_rad = (phase_rpm - phase_pwm)
    phase_diff_rad = (phase_diff_rad + np.pi) % (2 * np.pi) - np.pi
    
    gain = popt_rpm[0] / popt_pwm[0]
    phase_shift_deg = np.degrees(phase_diff_rad)
    
    return popt_rpm, gain, phase_shift_deg

# ==========================================
# 3. Data Processing & Plotting
# ==========================================
def analyze_bode_data():
    frequencies = [0.1, 0.5, 1.0]
    
    fig_comb, axes_comb = plt.subplots(3, 1, figsize=(10, 14), sharex=False)
    fig_comb.subplots_adjust(hspace=0.4)
    
    fig_nl, axes_nl = plt.subplots(3, 1, figsize=(10, 14), sharex=False)
    fig_nl.subplots_adjust(hspace=0.4)

    fig_l, axes_l = plt.subplots(3, 1, figsize=(10, 14), sharex=False)
    fig_l.subplots_adjust(hspace=0.4)
    
    # Text box properties for academic plots
    text_box_props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray')

    for i, freq in enumerate(frequencies):
        load_file = f'open_loop_sine_{freq}Hz_load.csv'
        noload_files = glob.glob(f'open_loop_sine_{freq}Hz_noload*.csv')
        noload_file = noload_files[0] if noload_files else None
        
        ax_c = axes_comb[i]
        ax2_c = ax_c.twinx()
        
        ax_nl = axes_nl[i]
        ax2_nl = ax_nl.twinx()
        
        ax_l = axes_l[i]
        ax2_l = ax_l.twinx()

        print(f"\n--- {freq} Hz Analysis ---")
        
        text_str_comb = ""
        
        # --- NO-LOAD ANALYSIS ---
        if noload_file:
            df_nl = pd.read_csv(noload_file)
            df_nl_steady = df_nl[df_nl['elapsed_s'] > 5.0]
            
            t_nl = df_nl_steady['elapsed_s'].to_numpy()
            pwm_nl = df_nl_steady['pwm'].to_numpy()
            rpm_nl = df_nl_steady['filtered_rpm'].to_numpy()
            
            fit_nl, gain_nl, phase_nl = extract_system_dynamics(t_nl, pwm_nl, rpm_nl, freq)
            
            print(f"NO-LOAD | Gain: {gain_nl:.3f} RPM/PWM | Phase: {phase_nl:.1f}° | Base RPM: {fit_nl[3]:.1f}")
            
            # Combined Graph Plotting
            ax_c.plot(df_nl['elapsed_s'], df_nl['filtered_rpm'], color='#2ca02c', label='No-Load RPM', alpha=0.5)
            ax_c.plot(t_nl, sine_func(t_nl, *fit_nl), color='#155d15', linestyle='--', linewidth=1.5, label='No-Load Fit')
            text_str_comb += f"No-Load: $K$={gain_nl:.3f}, $\\phi$={phase_nl:.1f}°\n"
            
            # No-Load Only Graph Plotting
            ax_nl.plot(df_nl['elapsed_s'], df_nl['filtered_rpm'], color='#2ca02c', label='No-Load RPM', alpha=0.9)
            ax_nl.plot(t_nl, sine_func(t_nl, *fit_nl), color='k', linestyle=':', linewidth=2, label='RPM Curve Fit')
            ax2_nl.plot(df_nl['elapsed_s'], df_nl['pwm'], color='#1f77b4', alpha=0.5, label='PWM Cmd')
            
            # Annotate No-Load Only Graph
            text_str_nl = f"System Gain ($K$): {gain_nl:.3f} RPM/PWM\nPhase Shift ($\\phi$): {phase_nl:.1f}°"
            ax_nl.text(0.02, 0.05, text_str_nl, transform=ax_nl.transAxes, fontsize=10, verticalalignment='bottom', bbox=text_box_props)
            
            ax_nl.set_title(f"{freq} Hz Sine Response (No-Load)")
            ax_nl.set_ylabel("RPM")
            ax2_nl.set_ylabel("PWM")
            ax_nl.grid(True, linestyle=':', alpha=0.7)
            
            lines, labels = ax_nl.get_legend_handles_labels()
            lines2, labels2 = ax2_nl.get_legend_handles_labels()
            ax2_nl.legend(lines + lines2, labels + labels2, loc='upper right')
        else:
            print(f"WARNING: No-Load file not found for {freq} Hz")

        # --- LOADED ANALYSIS ---
        if os.path.exists(load_file):
            df_l = pd.read_csv(load_file)
            df_l_steady = df_l[df_l['elapsed_s'] > 5.0]
            
            t_l = df_l_steady['elapsed_s'].to_numpy()
            pwm_l = df_l_steady['pwm'].to_numpy()
            rpm_l = df_l_steady['filtered_rpm'].to_numpy()
            
            fit_l, gain_l, phase_l = extract_system_dynamics(t_l, pwm_l, rpm_l, freq)
            
            print(f"LOADED  | Gain: {gain_l:.3f} RPM/PWM | Phase: {phase_l:.1f}° | Base RPM: {fit_l[3]:.1f}")
            
            # Combined Graph Plotting
            ax_c.plot(df_l['elapsed_s'], df_l['filtered_rpm'], color='#ff7f0e', label='Loaded RPM', alpha=0.8)
            ax_c.plot(t_l, sine_func(t_l, *fit_l), color='#8c4304', linestyle='-.', linewidth=2, label='Loaded Fit')
            ax2_c.plot(df_l['elapsed_s'], df_l['pwm'], color='#1f77b4', alpha=0.3, label='PWM Cmd')
            text_str_comb += f"Loaded: $K$={gain_l:.3f}, $\\phi$={phase_l:.1f}°"
            
            # Loaded Only Graph Plotting
            ax_l.plot(df_l['elapsed_s'], df_l['filtered_rpm'], color='#ff7f0e', label='Loaded RPM', alpha=0.9)
            ax_l.plot(t_l, sine_func(t_l, *fit_l), color='k', linestyle=':', linewidth=2, label='RPM Curve Fit')
            ax2_l.plot(df_l['elapsed_s'], df_l['pwm'], color='#1f77b4', alpha=0.5, label='PWM Cmd')
            
            # Annotate Loaded Only Graph
            text_str_l = f"System Gain ($K$): {gain_l:.3f} RPM/PWM\nPhase Shift ($\\phi$): {phase_l:.1f}°"
            ax_l.text(0.02, 0.05, text_str_l, transform=ax_l.transAxes, fontsize=10, verticalalignment='bottom', bbox=text_box_props)
            
            ax_l.set_title(f"{freq} Hz Sine Response (Loaded Tank)")
            ax_l.set_ylabel("RPM")
            ax2_l.set_ylabel("PWM")
            ax_l.grid(True, linestyle=':', alpha=0.7)
            
            lines, labels = ax_l.get_legend_handles_labels()
            lines2, labels2 = ax2_l.get_legend_handles_labels()
            ax2_l.legend(lines + lines2, labels + labels2, loc='upper right')
        else:
            print(f"ERROR: Loaded file not found: {load_file}")
            
        # --- COMBINED GRAPH FORMATTING & ANNOTATION ---
        if text_str_comb:
            ax_c.text(0.02, 0.05, text_str_comb.strip(), transform=ax_c.transAxes, fontsize=10, verticalalignment='bottom', bbox=text_box_props)
            
        ax_c.set_title(f"{freq} Hz Sine Response (Load vs No-Load)")
        ax_c.set_ylabel("RPM")
        ax2_c.set_ylabel("PWM")
        ax_c.grid(True, linestyle=':', alpha=0.7)
        
        lines, labels = ax_c.get_legend_handles_labels()
        lines2, labels2 = ax2_c.get_legend_handles_labels()
        ax2_c.legend(lines + lines2, labels + labels2, loc='upper right')

    axes_comb[-1].set_xlabel("Time (s)")
    axes_nl[-1].set_xlabel("Time (s)")
    axes_l[-1].set_xlabel("Time (s)")
    
    out_comb = os.path.join(output_dir, "fig1_bode_combined.png")
    out_nl = os.path.join(output_dir, "fig2_bode_noload_only.png")
    out_l = os.path.join(output_dir, "fig3_bode_loaded_only.png")
    
    fig_comb.savefig(out_comb)
    fig_nl.savefig(out_nl)
    fig_l.savefig(out_l)
    
    print(f"\nPlots saved to {output_dir}/:")
    print(f" - fig1_bode_combined.png")
    print(f" - fig2_bode_noload_only.png")
    print(f" - fig3_bode_loaded_only.png")

if __name__ == "__main__":
    analyze_bode_data()
"""
analyze_step.py
Purpose: Standardized step-response analyzer for MIXR-1 studies.
Computes a first-order fit, IMC PI tuning parameters, and appends a consistent
metadata-rich summary table for every step test.
"""
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

CANONICAL_CONFIGS = {
    "openloop_nofifo": "OpenLoop_NoFIFO",
    "openloop_fifo": "OpenLoop_FIFO",
    "pi_fifo": "PI_FIFO",
    "pi_nofifo": "PI_NoFIFO",
}


def canonicalize_mode_label(value):
    if value is None:
        return "OpenLoop_NoFIFO"
    normalized = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    normalized = normalized.replace("open_loop", "openloop").replace("closed_loop", "pi")
    for key, label in CANONICAL_CONFIGS.items():
        if key in normalized:
           return label
    if "fifo" in normalized:
        if "pi" in normalized:
           return "PI_FIFO"
        return "OpenLoop_FIFO"
    if "pi" in normalized:
        return "PI_NoFIFO"
    return "OpenLoop_NoFIFO"


def infer_step_config(file_path):
    filename = os.path.basename(file_path).lower()
    mode_label = canonicalize_mode_label(filename)
    controller = "PI" if "pi" in filename else "OpenLoop"
    fifo_enabled = "fifo" in filename
    if "pi" in filename and "fifo" not in filename:
        mode_label = "PI_NoFIFO"
        fifo_enabled = False
    if "fifo" in filename and "pi" not in filename:
        mode_label = "OpenLoop_FIFO"
        controller = "OpenLoop"
    return {
        "mode": mode_label,
        "controller": controller,
        "fifo_enabled": bool(fifo_enabled),
    }


# 1. File Selection Interface
csv_files = glob.glob("step_response_*.csv")
if not csv_files:
    print("Error: No 'step_response_X_Y.csv' files found in this directory.")
    sys.exit(1)

print("========================================")
print(" SELECT DATASET TO ANALYZE ")
print("========================================")
for i, f in enumerate(csv_files):
    print(f"[{i + 1}] {f}")

try:
    choice = int(input("\nEnter file number: ")) - 1
    if choice < 0 or choice >= len(csv_files):
        raise ValueError
    selected_file = csv_files[choice]
except ValueError:
    print("Invalid selection.")
    sys.exit(1)

file_parts = selected_file.replace(".csv", "").split("_")
base_pct = file_parts[-2]
step_pct = file_parts[-1]
config = infer_step_config(selected_file)

test_name = f"{base_pct}% to {step_pct}%"
step_label = f"{config['mode']} | {base_pct}% -> {step_pct}%"

# 2. Load and Shift Data
df = pd.read_csv(selected_file)
if "Time_s" not in df.columns:
    raise KeyError("Step response CSV must contain a 'Time_s' column.")
if "Raw_RPM" not in df.columns:
    raise KeyError("Step response CSV must contain a 'Raw_RPM' column.")

baseline_data = df[df["Time_s"] < 1.0]
step_data = df[df["Time_s"] >= 1.0].copy()

baseline_rpm = baseline_data["Raw_RPM"].mean() if not baseline_data.empty else 0.0
step_data["Time_s"] = step_data["Time_s"] - 1.0

t = step_data["Time_s"].to_numpy(dtype=float)
rpm = step_data["Raw_RPM"].to_numpy(dtype=float)

# 3. Curve Fitting
def first_order_step(t, K, A):
    return baseline_rpm + K * (1 - np.exp(-A * t))

p0 = [np.max(rpm) - baseline_rpm, 5.0]

try:
    popt, _ = curve_fit(first_order_step, t, rpm, p0=p0)
    K_fit = popt[0]
    A_fit = popt[1]
except RuntimeError:
    print("Error: Curve fit failed to converge.")
    sys.exit(1)

# 4. Math Engine (Control Theory & IMC Tuning)
settling_time_2pct = 4.0 / A_fit
rise_time_10_90 = 2.197 / A_fit
bandwidth_hz = A_fit / (2 * np.pi)

delta_pwm = (int(step_pct) - int(base_pct)) / 100.0 * 4095
K_plant = K_fit / delta_pwm if abs(delta_pwm) > 0 else np.nan
Kp_calc = 1.0 / K_plant if np.isfinite(K_plant) and abs(K_plant) > 0 else np.nan
Ki_calc = Kp_calc * A_fit if np.isfinite(Kp_calc) else np.nan

# 5. Output Results
print("\n" + "=" * 60)
print(f" METRICS FOR {step_label} STEP TEST ")
print("=" * 60)
print(f"Mode:                    {config['mode']}")
print(f"Controller:              {config['controller']}")
print(f"FIFO:                    {config['fifo_enabled']}")
print(f"Baseline RPM:            {baseline_rpm:.2f} RPM")
print(f"Steady-State Gain (K):   {K_fit:.2f} RPM (Delta)")
print(f"System Pole (A):         {A_fit:.2f}")
print(f"Rise Time (10% to 90%):  {rise_time_10_90:.4f} seconds")
print(f"Settling Time (2% error):{settling_time_2pct:.4f} seconds")
print(f"Mechanical Bandwidth:    {bandwidth_hz:.2f} Hz")
print("-" * 60)
print(" REQUIRED PI PARAMETERS (IMC CRITICALLY DAMPED) ")
print("-" * 60)
print(f"Plant Gain (K_plant):    {K_plant:.4f} RPM/PWM")
print(f"Proportional Gain (Kp):  {Kp_calc:.4f}")
print(f"Integral Gain (Ki):      {Ki_calc:.4f}")
print("=" * 60)

# 6. Export to Master Tuning Table
master_file = "tuning_table.csv"
file_exists = os.path.isfile(master_file)

with open(master_file, "a") as f:
    if not file_exists:
        f.write(
           "Test_Region,Mode,Controller,FIFO_Enabled,Baseline_PWM_pct,Step_PWM_pct,Baseline_RPM,Pole_A,Rise_Time_s,Settling_Time_s,Bandwidth_Hz,Kp,Ki\n"
        )
    f.write(
        f"{test_name},{config['mode']},{config['controller']},{int(config['fifo_enabled'])},{base_pct},{step_pct},{baseline_rpm:.2f},{A_fit:.4f},{rise_time_10_90:.4f},{settling_time_2pct:.4f},{bandwidth_hz:.4f},{Kp_calc:.4f},{Ki_calc:.4f}\n"
    )

print(f"\n[SUCCESS] Parameters appended to '{master_file}'")

# 7. Generate Thesis Plot
plt.figure(figsize=(10, 6))
plt.scatter(t, rpm, s=10, color="lightgray", label="Raw C++ Data (100Hz)")
plt.plot(t, first_order_step(t, K_fit, A_fit), "r-", linewidth=2, label=f"Fitted G(s): K={K_fit:.1f}, A={A_fit:.2f}")

plt.axvline(x=rise_time_10_90, color="orange", linestyle="--", alpha=0.7, label=f"Rise Time ({rise_time_10_90:.3f}s)")
plt.axvline(x=settling_time_2pct, color="blue", linestyle="--", alpha=0.7, label=f"Settling Time ({settling_time_2pct:.3f}s)")

plt.title(f"Motor Step Response ({step_label} PWM)")
plt.xlabel("Time (seconds)")
plt.ylabel("Rotational Speed (RPM)")
plt.legend()
plt.grid(True, linestyle=":", alpha=0.7)
plt.tight_layout()

plot_filename = f"plot_{base_pct}_{step_pct}.png"
plt.savefig(plot_filename, dpi=300)
print(f"[SUCCESS] Plot saved as '{plot_filename}'")
plt.close()

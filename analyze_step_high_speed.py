"""
analyze_step_high_speed.py
Purpose: Standardized step-response analyzer for high-speed motor tests.
Fits a first-order response from a non-zero baseline and exports metadata-rich
step metrics with canonical mode labels.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def canonicalize_mode_label(value):
    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if "fifo" in text:
        return "PI_FIFO" if "pi" in text else "OpenLoop_FIFO"
    if "pi" in text:
        return "PI_NoFIFO"
    return "OpenLoop_NoFIFO"


try:
    df = pd.read_csv("high_step_response_data.csv")
except FileNotFoundError:
    print("Error: 'high_step_response_data.csv' not found. Run the C++ logger first.")
    raise SystemExit(1)

# Calculate the baseline RPM from the first 1 second
baseline_data = df[df["Time_s"] < 1.0]
baseline_rpm = baseline_data["Raw_RPM"].mean() if not baseline_data.empty else 0.0

step_data = df[df["Time_s"] >= 1.0].copy()
step_data["Time_s"] = step_data["Time_s"] - 1.0

t = step_data["Time_s"].to_numpy(dtype=float)
rpm = step_data["Raw_RPM"].to_numpy(dtype=float)

# Modified Transfer Function: Accounts for the 70% PWM starting RPM
def first_order_step(t, K, A):
    return baseline_rpm + K * (1 - np.exp(-A * t))

# Initial guess: K is the step difference (Max RPM - Baseline RPM)
p0 = [np.max(rpm) - baseline_rpm, 5.0]

try:
    popt, _ = curve_fit(first_order_step, t, rpm, p0=p0)
    K_fit = popt[0]
    A_fit = popt[1]
except RuntimeError:
    print("Error: Curve fit failed to converge. Check if your data is extremely noisy.")
    raise SystemExit(1)

rise_time = 4.0 / A_fit
time_constant = 1.0 / A_fit
frequency = 1.0 / rise_time
min_sample_rate = frequency * 10.0
mode_label = canonicalize_mode_label("PI_FIFO")

print("\n" + "=" * 40)
print(" HIGH-SPEED TRANSFER FUNCTION METRICS ")
print("=" * 40)
print(f"Mode:                    {mode_label}")
print(f"Baseline RPM (70% PWM):  {baseline_rpm:.2f} RPM")
print(f"System Equation: RPM(t) = {baseline_rpm:.2f} + {K_fit:.2f} * (1 - e^(-{A_fit:.2f}t))")
print(f"Steady-State Gain (K):   {K_fit:.2f} RPM (Delta from baseline)")
print(f"System Pole (A):         {A_fit:.2f}")
print(f"Time Constant (Tau):     {time_constant:.4f} seconds")
print(f"Rise Time (4/A):         {rise_time:.4f} seconds")
print(f"Signal Frequency:        {frequency:.2f} Hz")
print(f"Minimum Sampling Rate:   {min_sample_rate:.2f} Hz")
print("=" * 40)

if min_sample_rate <= 100.0:
    print("\n[CONCLUSION] Your 100Hz C++ control loop is scientifically validated as FAST ENOUGH.\n")
else:
    print(f"\n[CONCLUSION] You must increase your C++ loop speed to > {min_sample_rate:.2f} Hz.\n")

plt.figure(figsize=(10, 6))
plt.scatter(t, rpm, s=10, color="lightgray", label="Raw C++ Data (100Hz)")
plt.plot(t, first_order_step(t, K_fit, A_fit), "r-", linewidth=2, label=f"Fitted Curve: {baseline_rpm:.1f} + {K_fit:.1f}(1 - e^{{-{A_fit:.2f}t}})")

plt.axvline(x=rise_time, color="blue", linestyle="--", alpha=0.7, label=f"Rise Time ({rise_time:.3f}s)")

plt.title(f"High-Speed Step Response ({mode_label})")
plt.xlabel("Time (seconds)")
plt.ylabel("Rotational Speed (RPM)")
plt.legend()
plt.grid(True, linestyle=":", alpha=0.7)
plt.tight_layout()
plot_filename = "thesis_step_response_1500.png"
plt.savefig(plot_filename, dpi=300)
print(f"[SUCCESS] Plot saved as '{plot_filename}'")
plt.close()

metadata = {
    "mode": mode_label,
    "controller": "PI",
    "fifo_enabled": True,
    "baseline_rpm": float(baseline_rpm),
    "gain_k": float(K_fit),
    "pole_a": float(A_fit),
    "time_constant_s": float(time_constant),
    "rise_time_s": float(rise_time),
    "signal_frequency_hz": float(frequency),
    "minimum_sampling_rate_hz": float(min_sample_rate),
}

metadata_df = pd.DataFrame([metadata])
metadata_out = "high_speed_step_summary.csv"
metadata_df.to_csv(metadata_out, index=False)
print(f"[SUCCESS] Metadata saved as '{metadata_out}'")

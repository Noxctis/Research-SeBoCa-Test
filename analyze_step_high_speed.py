"""
analyze_step_high_speed.py
Purpose: Parses step response data starting from a non-zero baseline, 
fits the adjusted first-order transfer function, and generates metrics.
"""
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

try:
    df = pd.read_csv("high_step_response_data.csv")
except FileNotFoundError:
    print("Error: 'step_response_data.csv' not found. Run the C++ logger first.")
    exit(1)

# Calculate the baseline RPM from the first 1 second
baseline_data = df[df['Time_s'] < 1.0]
baseline_rpm = baseline_data['Raw_RPM'].mean()

step_data = df[df['Time_s'] >= 1.0].copy()
step_data['Time_s'] = step_data['Time_s'] - 1.0 

t = step_data['Time_s'].values
rpm = step_data['Raw_RPM'].values

# Modified Transfer Function: Accounts for the 70% PWM starting RPM
def first_order_step(t, K, A):
    return baseline_rpm + K * (1 - np.exp(-A * t))

# Initial guess: K is the step difference (Max RPM - Baseline RPM)
p0 = [np.max(rpm) - baseline_rpm, 5.0]

try:
    popt, pcov = curve_fit(first_order_step, t, rpm, p0=p0)
    K_fit = popt[0]
    A_fit = popt[1]
except RuntimeError:
    print("Error: Curve fit failed to converge. Check if your data is extremely noisy.")
    exit(1)

rise_time = 4.0 / A_fit
time_constant = 1.0 / A_fit
frequency = 1.0 / rise_time
min_sample_rate = frequency * 10.0

print("\n" + "="*40)
print(" HIGH-SPEED TRANSFER FUNCTION METRICS ")
print("="*40)
print(f"Baseline RPM (70% PWM):   {baseline_rpm:.2f} RPM")
print(f"System Equation: RPM(t) = {baseline_rpm:.2f} + {K_fit:.2f} * (1 - e^(-{A_fit:.2f}t))")
print(f"Steady-State Gain (K):    {K_fit:.2f} RPM (Delta from baseline)")
print(f"System Pole (A):          {A_fit:.2f}")
print(f"Time Constant (Tau):      {time_constant:.4f} seconds")
print(f"Rise Time (4/A):          {rise_time:.4f} seconds")
print(f"Signal Frequency:         {frequency:.2f} Hz")
print(f"Minimum Sampling Rate:    {min_sample_rate:.2f} Hz")
print("="*40)

if min_sample_rate <= 100.0:
    print("\n[CONCLUSION] Your 100Hz C++ control loop is scientifically validated as FAST ENOUGH.\n")
else:
    print(f"\n[CONCLUSION] You must increase your C++ loop speed to > {min_sample_rate:.2f} Hz.\n")

plt.figure(figsize=(10, 6))
plt.scatter(t, rpm, s=10, color='lightgray', label='Raw C++ Data (100Hz)')
plt.plot(t, first_order_step(t, K_fit, A_fit), 'r-', linewidth=2, 
         label=f'Fitted Curve: {baseline_rpm:.1f} + {K_fit:.1f}(1 - e^{{-{A_fit:.2f}t}})')

plt.axvline(x=rise_time, color='blue', linestyle='--', alpha=0.7, 
            label=f'Rise Time ({rise_time:.3f}s)')

plt.title('High-Speed Step Response (70% -> 80% PWM)')
plt.xlabel('Time (seconds)')
plt.ylabel('Rotational Speed (RPM)')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.7)
plt.tight_layout()
plt.savefig("thesis_step_response_1500.png", dpi=300)
plt.show()
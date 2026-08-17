"""
analyze_step.py
Purpose: Parses step response data, fits a first-order transfer function, 
and generates metrics for PI controller tuning.
"""
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# 1. Load Data
try:
    df = pd.read_csv("step_response_data.csv")
except FileNotFoundError:
    print("Error: 'step_response_data.csv' not found. Run the C++ logger first.")
    exit(1)

# 2. Filter and Shift Data
# Isolate the data after the 1-second baseline
step_data = df[df['Time_s'] >= 1.0].copy()
# Shift time so the step mathematically starts at t = 0
step_data['Time_s'] = step_data['Time_s'] - 1.0 

t = step_data['Time_s'].values
rpm = step_data['Raw_RPM'].values

# 3. Define Transfer Function: RPM(t) = K * (1 - e^(-A * t))
def first_order_step(t, K, A):
    return K * (1 - np.exp(-A * t))

# 4. Perform Least-Squares Curve Fit
# Provide initial guesses to help the solver: 
# K = max RPM reached, A = 5.0 (arbitrary positive pole)
p0 = [np.max(rpm), 5.0]

try:
    popt, pcov = curve_fit(first_order_step, t, rpm, p0=p0)
    K_fit = popt[0]
    A_fit = popt[1]
except RuntimeError:
    print("Error: Curve fit failed to converge. Check if your data is extremely noisy or flat.")
    exit(1)

# 5. Calculate System Metrics
rise_time = 4.0 / A_fit
time_constant = 1.0 / A_fit
frequency = 1.0 / rise_time
min_sample_rate = frequency * 10.0

# 6. Console Output for Thesis
print("\n" + "="*40)
print(" TRANSFER FUNCTION METRICS ")
print("="*40)
print(f"System Equation: RPM(t) = {K_fit:.2f} * (1 - e^(-{A_fit:.2f}t))")
print(f"Steady-State Gain (K):    {K_fit:.2f} RPM")
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

# 7. Generate Thesis Plot
plt.figure(figsize=(10, 6))

# Plot raw data
plt.scatter(t, rpm, s=10, color='lightgray', label='Raw C++ Data (100Hz)')

# Plot fitted curve
plt.plot(t, first_order_step(t, K_fit, A_fit), 'r-', linewidth=2, 
         label=f'Fitted Curve: {K_fit:.1f}(1 - e^{{-{A_fit:.2f}t}})')

# Plot Rise Time line
plt.axvline(x=rise_time, color='blue', linestyle='--', alpha=0.7, 
            label=f'Rise Time ({rise_time:.3f}s)')

plt.title('Motor Step Response (10% PWM) - OS-10L with AMT102-V')
plt.xlabel('Time (seconds)')
plt.ylabel('Rotational Speed (RPM)')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.7)
plt.tight_layout()

# Save and show
plt.savefig("thesis_step_response.png", dpi=300)
plt.show()
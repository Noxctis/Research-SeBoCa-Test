import pandas as pd
import matplotlib.pyplot as plt

# Load the datasets
try:
    df_old = pd.read_csv('cet_1500rpm.csv')
    df_new = pd.read_csv('ram_buffered_test_1500.csv')
except FileNotFoundError:
    print("Ensure both 'io_bound_test.csv' and 'ram_buffered_test.csv' exist.")
    exit()

# Align column names
t_col_old = 't (s)' if 't (s)' in df_old.columns else 'elapsed_s'
t_col_new = 'elapsed_s'

plt.figure(figsize=(12, 6))

# Plot Old I/O Bound Timing
plt.plot(df_old[t_col_old], df_old['loop_period_us'] / 1000.0, 
         label=f"Old Code (SD Card I/O): Max Late = {df_old['late_us'].max():.1f} µs", 
         color='red', alpha=0.7)

# Plot New RAM Buffered Timing
plt.plot(df_new[t_col_new], df_new['loop_period_us'] / 1000.0, 
         label=f"New Code (RAM Buffer): Max Late = {df_new['late_us'].max():.1f} µs", 
         color='blue', alpha=0.9)

plt.axhline(10.0, color='black', linestyle='--', linewidth=2, label='Target (10ms)')

plt.title('Software Execution Jitter: File I/O vs. RAM Buffering', fontweight='bold')
plt.xlabel('Time (s)')
plt.ylabel('Loop Period (ms)')
plt.ylim(8, 25) # Scale to show the massive I/O spikes
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('latency_improvement_proof.png')
print("Saved 'latency_improvement_proof.png'")
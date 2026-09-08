import pandas as pd
import matplotlib.pyplot as plt

try:
    df_nofifo = pd.read_csv('cet_stress_nofifo.csv')
    df_fifo = pd.read_csv('cet_stress_fifo.csv')
    
    nofifo_period_std = df_nofifo['loop_period_us'].std()
    nofifo_max_late = df_nofifo['late_us'].max()

    fifo_period_std = df_fifo['loop_period_us'].std()
    fifo_max_late = df_fifo['late_us'].max()

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    ax1.plot(df_nofifo['elapsed_s'], df_nofifo['loop_period_us'] / 1000.0, color='#e41a1c', alpha=0.8, 
             label=f'Standard OS (Max Late: {nofifo_max_late/1000.0:.1f} ms)')
    ax1.axhline(10.0, color='black', linestyle='--', linewidth=1.5, label='Target (10 ms)')
    ax1.set_title(f'Standard Linux Scheduling under Load (Jitter SD: {nofifo_period_std:.1f} µs)', fontweight='bold')
    ax1.set_ylabel('Loop Period (ms)')
    ax1.set_ylim(0, 30) 
    ax1.legend(loc='upper right')

    ax2.plot(df_fifo['elapsed_s'], df_fifo['loop_period_us'] / 1000.0, color='#4daf4a', alpha=0.9, 
             label=f'Core 3 + FIFO (Max Late: {fifo_max_late/1000.0:.1f} ms)')
    ax2.axhline(10.0, color='black', linestyle='--', linewidth=1.5, label='Target (10 ms)')
    ax2.set_title(f'Real-Time Optimized Architecture under Load (Jitter SD: {fifo_period_std:.1f} µs)', fontweight='bold')
    ax2.set_ylabel('Loop Period (ms)')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylim(0, 30)
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig('os_determinism_comparison.png')
    print("Plot saved successfully.")

except Exception as e:
    print(f"Error: {e}")
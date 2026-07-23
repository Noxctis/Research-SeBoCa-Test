import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

datasets = [
    {'file': 'mixr1_log_20260722_164019.csv', 'label': '100Hz'},
    {'file': 'mixr1_log_20260722_164347.csv', 'label': '200Hz'},
    {'file': 'mixr1_log_20260722_164711.csv', 'label': '50Hz'}
]

today_date = datetime.today().strftime('%Y-%m-%d')

for data in datasets:
    df = pd.read_csv(data['file'])
    
    plt.figure(figsize=(10, 6))
    
    plt.plot(df['t (s)'], df['Raw RPM'], label='Raw RPM', color='red', alpha=0.4)
    plt.plot(df['t (s)'], df['Filtered RPM'], label='Filtered RPM', color='blue')
    
    plt.title(f"Motor Test ({data['label']}): Raw vs Filtered RPM")
    plt.xlabel('Time (s)')
    plt.ylabel('RPM')
    plt.legend()
    plt.grid(True)
    
    filename = f"motor_test_rpm_{data['label']}_{today_date}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
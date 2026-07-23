import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

df = pd.read_csv('water_surface_data.csv')

summary = df.groupby('Target_Distance_mm').agg(
    Raw_Avg=('Sensor_Avg_mm', 'mean'),
    Calib_Avg=('Calibrated_Reading_mm', 'mean')
).reset_index()

plt.figure(figsize=(10, 6))

plt.plot(summary['Target_Distance_mm'], summary['Target_Distance_mm'], 
         label='Ideal 1:1 Target', linestyle='--', color='black')

plt.plot(summary['Target_Distance_mm'], summary['Raw_Avg'], 
         label='Raw Sensor Output', marker='o', color='red')

plt.plot(summary['Target_Distance_mm'], summary['Calib_Avg'], 
         label='Calibrated Output', marker='s', color='blue')

plt.title('VL53L0X Water Surface Response')
plt.xlabel('Physical Target Distance (mm)')
plt.ylabel('Sensor Output (mm)')
plt.legend()
plt.grid(True)

today_date = datetime.today().strftime('%Y-%m-%d')
plt.savefig(f'water_surface_response_{today_date}.png', dpi=300, bbox_inches='tight')
plt.show()
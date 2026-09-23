import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from datetime import datetime

# ---------------------------------------------------------
# DIRECTORY & FILE CONFIGURATION
# ---------------------------------------------------------
INPUT_FILE = 'tank_zero_experiment real data 3.csv'

# Best Practice: Timestamp the output directory for strict version control
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = f'thesis_exports/raw_validation_{timestamp}'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# IEEE THESIS PLOT STYLING
# ---------------------------------------------------------
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'axes.grid': True,
    'grid.alpha': 0.6,
    'grid.linestyle': '--'
})

# ---------------------------------------------------------
# DATA PROCESSING & TABLE EXPORT
# ---------------------------------------------------------
df = pd.read_csv(INPUT_FILE).dropna(subset=['CalculatedFluid_mm', 'PhysicalMeasure_mm', 'TargetLevel_mm'])
df['Error_Raw'] = df['CalculatedFluid_mm'] - df['PhysicalMeasure_mm']

summary = df.groupby('TargetLevel_mm').agg(
    Mean_Physical=('PhysicalMeasure_mm', 'mean'),
    Mean_ToFAvg=('ToFAvg_mm', 'mean'),
    Mean_Calculated=('CalculatedFluid_mm', 'mean'),
    Mean_Error=('Error_Raw', 'mean'),
    Std_Error=('Error_Raw', 'std')
).reset_index()

# Files inside the timestamped directory can maintain clean, static names
table_path = os.path.join(OUTPUT_DIR, "raw_error_summary.csv")
summary.to_csv(table_path, index=False, float_format="%.2f")

# RMSE calculation using scikit-learn
rmse_raw = np.sqrt(mean_squared_error(df['PhysicalMeasure_mm'], df['CalculatedFluid_mm']))

# ---------------------------------------------------------
# FIGURE GENERATION
# ---------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# --- Panel 1: Parity Plot ---
max_val = max(df['PhysicalMeasure_mm'].max(), df['CalculatedFluid_mm'].max()) + 10
ax1.plot([0, max_val], [0, max_val], 'k-', linewidth=1.5, label='Ideal 1:1 Response', zorder=1)
ax1.scatter(df['PhysicalMeasure_mm'], df['CalculatedFluid_mm'], 
            c='#d62728', alpha=0.75, edgecolor='k', s=50, marker='o', 
            label=f'Uncalibrated ToF (RMSE: {rmse_raw:.2f} mm)', zorder=2)

ax1.set_title("Time-of-Flight Sensor Measurement Linearity", fontweight='bold')
ax1.set_xlabel("True Physical Depth (mm)")
ax1.set_ylabel("System Calculated Depth (mm)")
ax1.legend(loc='upper left', framealpha=1.0)
ax1.set_xlim(0, max_val)
ax1.set_ylim(0, max_val)

# --- Panel 2: Error Drift Profile ---
levels = df['TargetLevel_mm'].unique()
levels.sort()

means_raw = df.groupby('TargetLevel_mm')['Error_Raw'].mean()
stds_raw = df.groupby('TargetLevel_mm')['Error_Raw'].std()

ax2.axhline(0, color='k', linestyle='-', linewidth=1.5, zorder=1)
ax2.errorbar(levels, means_raw.loc[levels], yerr=stds_raw.loc[levels], fmt='-o', color='#d62728', 
             capsize=4, linewidth=1.5, markersize=6, markeredgecolor='k', label='Uncalibrated Error')

ax2.set_title("Absolute Measurement Error vs. Fluid Level", fontweight='bold')
ax2.set_xlabel("Target Fluid Level (mm)")
ax2.set_ylabel("Measurement Error (mm) [System - Physical]")
ax2.legend(loc='upper left', framealpha=1.0)

plt.tight_layout()

# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------
png_path = os.path.join(OUTPUT_DIR, "raw_linearity_profile.png")
pdf_path = os.path.join(OUTPUT_DIR, "raw_linearity_profile.pdf")

plt.savefig(png_path, dpi=300)
plt.savefig(pdf_path)

print(f"[SUCCESS] Exported graphs to '{png_path}' and '{pdf_path}'")
print(f"[SUCCESS] Exported table to '{table_path}'")
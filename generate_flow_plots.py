import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from scipy.stats import linregress
from datetime import datetime

# ---------------------------------------------------------
# DIRECTORY & FILE CONFIGURATION
# ---------------------------------------------------------
INPUT_FILE = 'tank_zero_experiment real data 3.csv'
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = f'thesis_exports/raw_validation_{timestamp}'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# IEEE THESIS PLOT STYLING
# ---------------------------------------------------------
plt.rcParams.update({
    'font.size': 11, 'font.family': 'serif', 'axes.labelsize': 12,
    'axes.titlesize': 13, 'legend.fontsize': 10, 'figure.dpi': 300,
    'xtick.labelsize': 10, 'ytick.labelsize': 10, 'axes.grid': True,
    'grid.alpha': 0.6, 'grid.linestyle': '--'
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

summary.to_csv(os.path.join(OUTPUT_DIR, "raw_error_summary.csv"), index=False, float_format="%.2f")

# ---------------------------------------------------------
# CALCULATIONS (Pylance Type-Safe Fix via NumPy)
# ---------------------------------------------------------
rmse_raw = float(np.sqrt(mean_squared_error(df['PhysicalMeasure_mm'], df['CalculatedFluid_mm'])))

# Convert to pure arrays and pass through np.asarray() so Pylance statically recognizes the floats
x_data = df['PhysicalMeasure_mm'].to_numpy(dtype=float)
y_data = df['CalculatedFluid_mm'].to_numpy(dtype=float)

reg_res = np.asarray(linregress(x_data, y_data))
slope = float(reg_res[0])
intercept = float(reg_res[1])
r_value = float(reg_res[2])

max_val = max(df['PhysicalMeasure_mm'].max(), df['CalculatedFluid_mm'].max()) + 10
levels = df['TargetLevel_mm'].unique()
levels.sort()
means_raw = df.groupby('TargetLevel_mm')['Error_Raw'].mean()
stds_raw = df.groupby('TargetLevel_mm')['Error_Raw'].std()

# Format the intercept sign correctly to prevent "+ -0.14"
intercept_str = f"+ {intercept:.4f}" if intercept >= 0 else f"- {abs(intercept):.4f}"

# ---------------------------------------------------------
# PLOTTING FUNCTIONS
# ---------------------------------------------------------
def plot_parity(ax):
    ax.plot([0, max_val], [0, max_val], 'k-', linewidth=1.5, label='Ideal 1:1 Response', zorder=1)
    ax.scatter(df['PhysicalMeasure_mm'], df['CalculatedFluid_mm'], 
               c='#d62728', alpha=0.75, edgecolor='k', s=50, marker='o', 
               label=fr'Uncalibrated ToF (RMSE: {rmse_raw:.2f} mm)', zorder=2)
    ax.set_title("System Measurement Linearity", fontweight='bold')
    ax.set_xlabel("True Physical Depth (mm)")
    ax.set_ylabel("System Calculated Depth (mm)")
    ax.legend(loc='upper left', framealpha=1.0)
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)

def plot_regression(ax):
    x_vals = np.array([0, max_val])
    y_vals = intercept + slope * x_vals
    ax.scatter(df['PhysicalMeasure_mm'], df['CalculatedFluid_mm'], 
               c='#1f77b4', alpha=0.6, edgecolor='k', s=40, label='Raw Data Points', zorder=2)
    
    label_str = fr"Linear Fit: \(y = {slope:.4f}x {intercept_str}\)" + "\n" + fr"\(R^2 = {r_value**2:.4f}\)"
    
    ax.plot(x_vals, y_vals, 'b--', linewidth=2, label=label_str, zorder=3)
    ax.set_title("Linear Regression Analysis", fontweight='bold')
    ax.set_xlabel("True Physical Depth (mm)")
    ax.set_ylabel("System Calculated Depth (mm)")
    ax.legend(loc='upper left', framealpha=1.0)
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)

def plot_error(ax):
    ax.axhline(0, color='k', linestyle='-', linewidth=1.5, zorder=1)
    ax.errorbar(levels, means_raw.loc[levels], yerr=stds_raw.loc[levels], fmt='-o', color='#d62728', 
                capsize=4, linewidth=1.5, markersize=6, markeredgecolor='k', label='Uncalibrated Error')
    ax.set_title("Absolute Error vs. Target Level", fontweight='bold')
    ax.set_xlabel("Target Fluid Level (mm)")
    ax.set_ylabel("Measurement Error (mm) [System - Physical]")
    ax.legend(loc='upper left', framealpha=1.0)

# ---------------------------------------------------------
# FIGURE GENERATION & EXPORT
# ---------------------------------------------------------
# 1. Combined Plot
fig_combined, axes = plt.subplots(1, 3, figsize=(18, 6))
plot_parity(axes[0])
plot_regression(axes[1])
plot_error(axes[2])
fig_combined.tight_layout()
fig_combined.savefig(os.path.join(OUTPUT_DIR, "combined_linearity_regression_profile.png"), dpi=300)
fig_combined.savefig(os.path.join(OUTPUT_DIR, "combined_linearity_regression_profile.pdf"))
plt.close(fig_combined)

# 2. Separate Plot 1: Parity
fig1, ax1 = plt.subplots(figsize=(7, 6))
plot_parity(ax1)
fig1.tight_layout()
fig1.savefig(os.path.join(OUTPUT_DIR, "fig1_system_measurement_linearity.png"), dpi=300)
fig1.savefig(os.path.join(OUTPUT_DIR, "fig1_system_measurement_linearity.pdf"))
plt.close(fig1)

# 3. Separate Plot 2: Regression
fig2, ax2 = plt.subplots(figsize=(7, 6))
plot_regression(ax2)
fig2.tight_layout()
fig2.savefig(os.path.join(OUTPUT_DIR, "fig2_linear_regression_analysis.png"), dpi=300)
fig2.savefig(os.path.join(OUTPUT_DIR, "fig2_linear_regression_analysis.pdf"))
plt.close(fig2)

# 4. Separate Plot 3: Error Profile
fig3, ax3 = plt.subplots(figsize=(7, 6))
plot_error(ax3)
fig3.tight_layout()
fig3.savefig(os.path.join(OUTPUT_DIR, "fig3_absolute_error_profile.png"), dpi=300)
fig3.savefig(os.path.join(OUTPUT_DIR, "fig3_absolute_error_profile.pdf"))
plt.close(fig3)

print(f"[SUCCESS] All individual and combined plots saved to '{OUTPUT_DIR}/'")
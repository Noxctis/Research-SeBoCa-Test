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
OUTPUT_DIR = f'thesis_exports/presentation_validation_{timestamp}'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# PRESENTATION / THESIS PLOT STYLING
# ---------------------------------------------------------
# Increased font sizes and line weights for PowerPoint visibility
plt.rcParams.update({
    'font.size': 14, 
    'font.family': 'serif', 
    'axes.labelsize': 16,
    'axes.titlesize': 18, 
    'axes.titleweight': 'bold',
    'legend.fontsize': 12, 
    'figure.dpi': 300,
    'xtick.labelsize': 12, 
    'ytick.labelsize': 12, 
    'axes.grid': True,
    'grid.alpha': 0.6, 
    'grid.linestyle': '--',
    'lines.linewidth': 2.5,
    'lines.markersize': 8
})

# ---------------------------------------------------------
# DATA PROCESSING & METRICS
# ---------------------------------------------------------
df = pd.read_csv(INPUT_FILE).dropna(subset=['CalculatedFluid_mm', 'PhysicalMeasure_mm', 'TargetLevel_mm'])
df['Error_Raw'] = df['CalculatedFluid_mm'] - df['PhysicalMeasure_mm']
df['Error_Percent'] = (df['Error_Raw'].abs() / df['PhysicalMeasure_mm']) * 100

summary = df.groupby('TargetLevel_mm').agg(
    Mean_Physical=('PhysicalMeasure_mm', 'mean'),
    Mean_Calculated=('CalculatedFluid_mm', 'mean'),
    Mean_Error=('Error_Raw', 'mean'),
    Std_Error=('Error_Raw', 'std'),
    Mean_Percent_Error=('Error_Percent', 'mean')
).reset_index()

# Rounding for clean presentation table
summary_rounded = summary.copy()
summary_rounded = summary_rounded.round(2)
summary_rounded.columns = [
    'Target (mm)', 'True Avg (mm)', 'Calc Avg (mm)', 
    'Mean Error (mm)', 'Std Dev (mm)', 'Avg % Error'
]

summary.to_csv(os.path.join(OUTPUT_DIR, "validation_summary.csv"), index=False, float_format="%.2f")

# ---------------------------------------------------------
# CALCULATIONS
# ---------------------------------------------------------
rmse_raw = float(np.sqrt(mean_squared_error(df['PhysicalMeasure_mm'], df['CalculatedFluid_mm'])))

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
means_percent = df.groupby('TargetLevel_mm')['Error_Percent'].mean()

intercept_str = f"+ {intercept:.4f}" if intercept >= 0 else f"- {abs(intercept):.4f}"

# ---------------------------------------------------------
# PLOTTING FUNCTIONS
# ---------------------------------------------------------
def plot_parity(ax):
    ax.plot([0, max_val], [0, max_val], 'k-', label='Ideal 1:1 Response', zorder=1)
    ax.scatter(df['PhysicalMeasure_mm'], df['CalculatedFluid_mm'], 
               c='#d62728', alpha=0.75, edgecolor='k', s=80, marker='o', 
               label=f'ToF Sensor (RMSE: {rmse_raw:.2f} mm)', zorder=2)
    ax.set_title("Measurement Linearity")
    ax.set_xlabel("True Physical Depth (mm)")
    ax.set_ylabel("System Calculated Depth (mm)")
    ax.legend(loc='upper left', framealpha=1.0)
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)

def plot_regression(ax):
    x_vals = np.array([0, max_val])
    y_vals = intercept + slope * x_vals
    ax.scatter(df['PhysicalMeasure_mm'], df['CalculatedFluid_mm'], 
               c='#1f77b4', alpha=0.6, edgecolor='k', s=60, label='Raw Data Points', zorder=2)
    
    label_str = f"Linear Fit: y = {slope:.4f}x {intercept_str}\nR² = {r_value**2:.4f}"
    
    ax.plot(x_vals, y_vals, 'b--', label=label_str, zorder=3)
    ax.set_title("Linear Regression Analysis")
    ax.set_xlabel("True Physical Depth (mm)")
    ax.set_ylabel("System Calculated Depth (mm)")
    ax.legend(loc='upper left', framealpha=1.0)
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)

def plot_error(ax):
    ax.axhline(0, color='k', linestyle='-', zorder=1)
    ax.errorbar(levels, means_raw.loc[levels], yerr=stds_raw.loc[levels], fmt='-o', color='#d62728', 
                capsize=6, capthick=2, markersize=8, markeredgecolor='k', label='Absolute Error')
    ax.set_title("Absolute Error vs. Target Level")
    ax.set_xlabel("Target Fluid Level (mm)")
    ax.set_ylabel("Error (mm) [System - Physical]")
    ax.legend(loc='upper left', framealpha=1.0)

def plot_percent_error(ax):
    ax.plot(levels, means_percent.loc[levels], '-o', color='#2ca02c', 
            markersize=8, markeredgecolor='k', label='Mean % Error')
    
    # Annotate points for PPT readability
    for x, y in zip(levels, means_percent.loc[levels]):
        ax.annotate(f'{y:.2f}%', (x, y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=12)
        
    ax.set_title("Percentage Error Profile")
    ax.set_xlabel("Target Fluid Level (mm)")
    ax.set_ylabel("Mean Percentage Error (%)")
    ax.set_ylim(0, means_percent.max() + 3)
    ax.legend(loc='upper left', framealpha=1.0)

def generate_table_image():
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(cellText=summary_rounded.values,
                     colLabels=summary_rounded.columns,
                     cellLoc='center',
                     loc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table.scale(1, 2)
    
    # Style headers
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#40466e')
        elif i % 2 == 0:
            cell.set_facecolor('#f1f1f2')
            
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "presentation_data_table.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

# ---------------------------------------------------------
# FIGURE GENERATION & EXPORT
# ---------------------------------------------------------
# 1. Separate Plot 1: Parity
fig1, ax1 = plt.subplots(figsize=(8, 7))
plot_parity(ax1)
fig1.tight_layout()
fig1.savefig(os.path.join(OUTPUT_DIR, "fig1_system_measurement_linearity.png"))
plt.close(fig1)

# 2. Separate Plot 2: Regression
fig2, ax2 = plt.subplots(figsize=(8, 7))
plot_regression(ax2)
fig2.tight_layout()
fig2.savefig(os.path.join(OUTPUT_DIR, "fig2_linear_regression_analysis.png"))
plt.close(fig2)

# 3. Separate Plot 3: Absolute Error Profile
fig3, ax3 = plt.subplots(figsize=(8, 7))
plot_error(ax3)
fig3.tight_layout()
fig3.savefig(os.path.join(OUTPUT_DIR, "fig3_absolute_error_profile.png"))
plt.close(fig3)

# 4. Separate Plot 4: Percent Error Profile
fig4, ax4 = plt.subplots(figsize=(8, 7))
plot_percent_error(ax4)
fig4.tight_layout()
fig4.savefig(os.path.join(OUTPUT_DIR, "fig4_percent_error_profile.png"))
plt.close(fig4)

# 5. Combined Grid Plot (2x2) for dense slides
fig_grid, axes = plt.subplots(2, 2, figsize=(16, 14))
plot_parity(axes[0, 0])
plot_regression(axes[0, 1])
plot_error(axes[1, 0])
plot_percent_error(axes[1, 1])
fig_grid.tight_layout()
fig_grid.savefig(os.path.join(OUTPUT_DIR, "combined_2x2_validation_grid.png"))
plt.close(fig_grid)

# 6. Generate High-Res Table Image
generate_table_image()

print(f"[SUCCESS] Exported presentation-ready plots and table to '{OUTPUT_DIR}/'")
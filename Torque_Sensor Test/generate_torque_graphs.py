import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import numpy as np
import os
from datetime import datetime

# ==========================================
# 1. Configuration & Thesis Formatting
# ==========================================
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'lines.linewidth': 1.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

date_str = datetime.now().strftime("%Y%m%d")
output_dir = f"Loadcell_Thesis_Plots_{date_str}"
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory created: {output_dir}/")

# Load and prepare load cell data
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "loadcell_test_20261012_210846.csv")
try:
    df = pd.read_csv(file_path)
except FileNotFoundError as e:
    print(f"Error loading CSV file: {e}")
    exit(1)

df['error_Nm'] = df['reading'] - df['expected_torque_Nm']
df['percent_error'] = (df['error_Nm'] / df['expected_torque_Nm']) * 100

# Set seaborn theme for gridlines while keeping matplotlib rcParams
sns.set_theme(style="whitegrid", rc=plt.rcParams)

# ==========================================
# 2. Individual Plot Generation Functions
# ==========================================

def plot_linearity():
    fig, ax = plt.subplots(figsize=(8, 6))
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(df['expected_torque_Nm'], df['reading'])
    ax.scatter(df['expected_torque_Nm'], df['reading'], alpha=0.7, label='Measured Data', color='#1f77b4')
    
    x_vals = np.array([df['expected_torque_Nm'].min(), df['expected_torque_Nm'].max()])
    ax.plot(x_vals, intercept + slope * x_vals, 'r--', 
            label=f'Fit: y={slope:.4f}x + {intercept:.4f}\n$R^2$={r_value**2:.6f}')
    
    ax.set_title('Linearity: Measured vs Expected Torque')
    ax.set_xlabel('Expected Torque (Nm)')
    ax.set_ylabel('Measured Torque (Nm)')
    ax.legend(loc='best')
    
    plt.savefig(os.path.join(output_dir, "fig1_loadcell_linearity.png"))
    plt.close(fig)

def plot_residuals():
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sns.scatterplot(data=df, x='expected_torque_Nm', y='error_Nm', hue='weight_g', palette='viridis', ax=ax)
    ax.axhline(0, color='red', linestyle='--')
    
    # Manually setting y-limits to +/- 0.01 Nm to provide visual context 
    # against the sensor's full 0.25 Nm range, preventing micro-errors from looking huge.
    ax.set_ylim(-0.01, 0.01)
    
    ax.set_title('Residuals: Absolute Error vs Expected Torque')
    ax.set_xlabel('Expected Torque (Nm)')
    ax.set_ylabel('Error (Measured - Expected) [Nm]')
    ax.legend(title="Weight (g)", loc='best')
    
    plt.savefig(os.path.join(output_dir, "fig2_loadcell_residuals.png"))
    plt.close(fig)

def plot_relative_error():
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sns.scatterplot(data=df, x='expected_torque_Nm', y='percent_error', hue='weight_g', palette='viridis', ax=ax)
    ax.axhline(0, color='red', linestyle='--')
    
    # Manually setting y-limits to +/- 5% to show how tightly bound the percentage error actually is.
    ax.set_ylim(-5.0, 5.0)
    
    ax.set_title('Relative Error: Percentage Error vs Expected Torque')
    ax.set_xlabel('Expected Torque (Nm)')
    ax.set_ylabel('Percentage Error (%)')
    ax.legend(title="Weight (g)", loc='best')
    
    plt.savefig(os.path.join(output_dir, "fig3_loadcell_relative_error.png"))
    plt.close(fig)

def plot_repeatability():
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sns.boxplot(data=df, x='weight_g', y='reading', ax=ax, palette='light:gray')
    sns.stripplot(data=df, x='weight_g', y='reading', color='black', alpha=0.6, ax=ax)
    
    ax.set_title('Repeatability: Spread of Readings per Weight')
    ax.set_xlabel('Applied Weight (g)')
    ax.set_ylabel('Measured Torque (Nm)')
    ax.tick_params(axis='x', rotation=45)
    
    plt.savefig(os.path.join(output_dir, "fig4_loadcell_repeatability.png"))
    plt.close(fig)

# ==========================================
# Execute Script
# ==========================================
if __name__ == "__main__":
    print("Generating load cell thesis plots...")
    plot_linearity()
    plot_residuals()
    plot_relative_error()
    plot_repeatability()
    print(f"Complete. All individual thesis-formatted plots saved to {output_dir}/")
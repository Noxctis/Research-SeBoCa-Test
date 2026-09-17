import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Reset to default style for white background
plt.style.use('default')

# Define light theme colors (GitHub Light Theme palette for consistency)
color_red = '#d73a49'
color_green = '#28a745'
color_blue = '#0366d6'
color_text = '#24292e'
color_grid = '#e1e4e8'
color_box = '#f6f8fa'

# ==========================================
# DIAGRAM 1: CONCEPTUAL BANDWIDTH & THE SPRING ANALOGY
# ==========================================
fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
ax.set_facecolor('white')
ax.axis('off')

# Title
plt.text(0.5, 0.95, "What is Controller Bandwidth?", 
         ha='center', va='center', fontsize=20, fontweight='bold', color=color_blue)

# Left Side: Low Bandwidth
plt.text(0.25, 0.8, "LOW Bandwidth (0.5 rad/s)", 
         ha='center', va='center', fontsize=16, fontweight='bold', color=color_green)
plt.text(0.25, 0.72, "The \"Soft Spring\"", 
         ha='center', va='center', fontsize=14, fontstyle='italic', color='#586069')

# Draw a soft, stretched spring
t = np.linspace(0, 4*np.pi, 100)
x_spring_soft = 0.25 + 0.05 * np.sin(t)
y_spring_soft = np.linspace(0.65, 0.45, 100)
ax.plot(x_spring_soft, y_spring_soft, color=color_green, lw=2)

# Mass (Impeller) heavily deflected by water
ax.add_patch(patches.Rectangle((0.15, 0.35), 0.2, 0.1, facecolor=color_box, edgecolor=color_green, lw=2))
plt.text(0.25, 0.4, "IMPELLER", ha='center', va='center', color=color_text, fontweight='bold')
# Heavy water force pushing down
ax.arrow(0.25, 0.6, 0, -0.1, head_width=0.03, head_length=0.03, fc=color_blue, ec=color_blue, lw=3)
plt.text(0.32, 0.55, "Heavy\nFluid\nForce", ha='center', va='center', color=color_blue, fontweight='bold')

plt.text(0.25, 0.25, "Result: Gets crushed by\nfluid turbulence. Sluggish\nrecovery (Underpowered).", 
         ha='center', va='center', fontsize=12, color=color_red)

# Right Side: High Bandwidth
plt.text(0.75, 0.8, "HIGH Bandwidth (1.0 rad/s)", 
         ha='center', va='center', fontsize=16, fontweight='bold', color=color_red)
plt.text(0.75, 0.72, "The \"Stiff Spring\"", 
         ha='center', va='center', fontsize=14, fontstyle='italic', color='#586069')

# Draw a stiff, compressed spring
t = np.linspace(0, 12*np.pi, 300)
x_spring_stiff = 0.75 + 0.05 * np.sin(t)
y_spring_stiff = np.linspace(0.65, 0.55, 300)
ax.plot(x_spring_stiff, y_spring_stiff, color=color_red, lw=4)

# Mass (Impeller) barely deflected by water
ax.add_patch(patches.Rectangle((0.65, 0.45), 0.2, 0.1, facecolor=color_box, edgecolor=color_red, lw=2))
plt.text(0.75, 0.5, "IMPELLER", ha='center', va='center', color=color_text, fontweight='bold')
# Heavy water force pushing down
ax.arrow(0.75, 0.7, 0, -0.05, head_width=0.03, head_length=0.03, fc=color_blue, ec=color_blue, lw=3)
plt.text(0.82, 0.65, "Heavy\nFluid\nForce", ha='center', va='center', color=color_blue, fontweight='bold')

plt.text(0.75, 0.35, "Result: Fights back instantly.\nHolds target speed against\nheavy resistance (Dominant).", 
         ha='center', va='center', fontsize=12, color=color_green)

# Divider
ax.plot([0.5, 0.5], [0.1, 0.85], color=color_grid, lw=2, linestyle='--')

plt.savefig('bandwidth_concept_white.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

# ==========================================
# DIAGRAM 2: CONTROLLER EFFORT (PWM INJECTION)
# ==========================================
t = np.linspace(0, 10, 500)
disturbance_t = 2.0

# Simulate Controller Effort (Power injected into motor)
pwm_base = 30
pwm_soft = np.full_like(t, pwm_base, dtype=float)
pwm_stiff = np.full_like(t, pwm_base, dtype=float)

mask = t >= disturbance_t
t_active = t[mask] - disturbance_t

# Soft controller reacts slowly, takes a long time to ramp up power
pwm_soft[mask] = pwm_base + 30 * (1 - np.exp(-0.8 * t_active))
# Stiff controller spikes power instantly to fight the water, then settles
pwm_stiff[mask] = pwm_base + 45 * (1 - np.exp(-4.0 * t_active)) * np.exp(-0.5 * t_active) + 30 * (1 - np.exp(-4.0 * t_active))

fig2, ax2 = plt.subplots(figsize=(10, 5), facecolor='white')
ax2.set_facecolor('white')
ax2.tick_params(colors=color_text)
for spine in ax2.spines.values():
    spine.set_color('#d1d5da')

ax2.plot(t, pwm_stiff, color=color_red, lw=3, label='1.0 rad/s (High Bandwidth / Stiff Spring)')
ax2.plot(t, pwm_soft, color=color_green, lw=3, label='0.5 rad/s (Low Bandwidth / Soft Spring)')

ax2.axvline(disturbance_t, color=color_blue, linestyle='--', lw=2, label='Massive Fluid Disturbance (Baffles/Water)')

ax2.set_title("Controller Effort: How the System Fights Back", color=color_text, fontweight='bold', fontsize=14)
ax2.set_xlabel("Time (s)", color=color_text, fontsize=12)
ax2.set_ylabel("Power Injection (PWM %)", color=color_text, fontsize=12)
ax2.grid(True, color=color_grid, linestyle='-', alpha=1.0)
ax2.legend(facecolor='white', edgecolor='#d1d5da', labelcolor=color_text, fontsize=11)

# Annotations
ax2.annotate('Instant aggressive power spike\nto punch through water drag', 
             xy=(2.2, 60), xytext=(3.5, 65),
             arrowprops=dict(facecolor=color_red, shrink=0.05, width=1, headwidth=8, edgecolor='none'),
             color=color_red, fontweight='bold')

ax2.annotate('Sluggish, weak power increase.\nMotor gets dragged down.', 
             xy=(4, 52), xytext=(5.5, 45),
             arrowprops=dict(facecolor=color_green, shrink=0.05, width=1, headwidth=8, edgecolor='none'),
             color=color_green, fontweight='bold')

plt.tight_layout()
plt.savefig('controller_effort_white.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("White background diagrams generated.")
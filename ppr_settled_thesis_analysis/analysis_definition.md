# Settled Analysis Definition

Only samples from 1 to 100 seconds are considered. For each 10-second PWM command step, only the interior seconds are retained: 1-9 s, 11-19 s, ..., 91-99 s. The first and last second of each step are excluded to remove command-boundary transients. Standard deviation is calculated from RPM samples inside each settled interval. The sampling-window effect is 20 ms minus 10 ms at identical PPR and PWM. PPR effects are pairwise differences at identical PWM and sampling window.

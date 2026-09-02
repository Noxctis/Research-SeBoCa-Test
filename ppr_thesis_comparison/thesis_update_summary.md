# Encoder Resolution and PWM-Step Comparison

PWM bins are fixed at 10 seconds: 0-10 s = 0%, 10-20 s = 10%, continuing by 10 percentage points. All PPR values supplied are included in the all-resolution tables: 48, 96, 100, 125, 192, 200, 250, and 256 PPR.

## All-Resolution Summary

| ppr | sampling_window_ms | pwm_steps_measured | active_pwm_start_percent | active_pwm_end_percent | mean_of_pwm_medians_rpm | mean_within_step_sd_rpm | worst_within_step_sd_rpm | mean_filtered_sd_rpm | total_revolution_increment | peak_raw_rpm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 48 | 10 | 12 | 10 | 110 | 1242.22 | 103.94 | 716.81 | 102.16 | 2304 | 2621.03 |
| 48 | 20 | 12 | 10 | 110 | 1247.74 | 99.7 | 695.09 | 101.13 | 2305 | 2573.2 |
| 96 | 10 | 13 | 10 | 110 | 1245.35 | 97.65 | 628.09 | 95.63 | 2303 | 2618.95 |
| 96 | 20 | 13 | 10 | 110 | 1251.51 | 88.69 | 596.5 | 90.38 | 2328 | 2554.68 |
| 100 | 10 | 13 | 10 | 110 | 1258.95 | 87.87 | 582.34 | 87.29 | 2333 | 2609.65 |
| 100 | 20 | 13 | 10 | 110 | 1258.37 | 92.27 | 624.46 | 93.93 | 2338 | 2578.97 |
| 125 | 10 | 12 | 10 | 110 | 1258.64 | 95.79 | 640.82 | 95.23 | 2334 | 2614.17 |
| 125 | 20 | 12 | 10 | 110 | 1259.06 | 104.95 | 756.48 | 107.05 | 2347 | 2567.96 |
| 192 | 10 | 12 | 10 | 110 | 1257.8 | 95.05 | 624.94 | 93.43 | 2322 | 2627.34 |
| 192 | 20 | 13 | 10 | 110 | 1256.21 | 89.49 | 599.52 | 89.89 | 2337 | 2556.37 |
| 200 | 10 | 12 | 10 | 110 | 1250.23 | 99.23 | 669.1 | 97.32 | 2313 | 2609.53 |
| 200 | 20 | 12 | 10 | 110 | 1252.36 | 103.67 | 704.21 | 103.97 | 2326 | 2546.9 |
| 250 | 10 | 12 | 10 | 110 | 1247.76 | 118.14 | 696.24 | 102.45 | 2307 | 6102.32 |
| 250 | 20 | 13 | 10 | 110 | 1250.29 | 111.18 | 588.52 | 97.26 | 2317 | 4974.73 |
| 256 | 10 | 12 | 10 | 110 | 1254.09 | 151.14 | 771.42 | 114.01 | 2327 | 7119.38 |
| 256 | 20 | 12 | 10 | 110 | 1257.54 | 132.61 | 718.83 | 108.97 | 2342 | 5721.63 |

## 20 ms Minus 10 ms

| ppr | pwm_steps_measured_10ms | pwm_steps_measured_20ms | pwm_steps_measured_20ms_minus_10ms | pwm_steps_measured_percent_change | active_pwm_start_percent_10ms | active_pwm_start_percent_20ms | active_pwm_start_percent_20ms_minus_10ms | active_pwm_start_percent_percent_change | active_pwm_end_percent_10ms | active_pwm_end_percent_20ms | active_pwm_end_percent_20ms_minus_10ms | active_pwm_end_percent_percent_change | mean_of_pwm_medians_rpm_10ms | mean_of_pwm_medians_rpm_20ms | mean_of_pwm_medians_rpm_20ms_minus_10ms | mean_of_pwm_medians_rpm_percent_change | mean_within_step_sd_rpm_10ms | mean_within_step_sd_rpm_20ms | mean_within_step_sd_rpm_20ms_minus_10ms | mean_within_step_sd_rpm_percent_change | worst_within_step_sd_rpm_10ms | worst_within_step_sd_rpm_20ms | worst_within_step_sd_rpm_20ms_minus_10ms | worst_within_step_sd_rpm_percent_change | mean_filtered_sd_rpm_10ms | mean_filtered_sd_rpm_20ms | mean_filtered_sd_rpm_20ms_minus_10ms | mean_filtered_sd_rpm_percent_change | total_revolution_increment_10ms | total_revolution_increment_20ms | total_revolution_increment_20ms_minus_10ms | total_revolution_increment_percent_change | peak_raw_rpm_10ms | peak_raw_rpm_20ms | peak_raw_rpm_20ms_minus_10ms | peak_raw_rpm_percent_change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 48 | 12.0 | 12.0 | 0.0 | 0.0 | 10.0 | 10.0 | 0.0 | 0.0 | 110.0 | 110.0 | 0.0 | 0.0 | 1242.22 | 1247.74 | 5.52 | 0.44 | 103.94 | 99.7 | -4.24 | -4.08 | 716.81 | 695.09 | -21.72 | -3.03 | 102.16 | 101.13 | -1.04 | -1.01 | 2304.0 | 2305.0 | 1.0 | 0.04 | 2621.03 | 2573.2 | -47.83 | -1.82 |
| 96 | 13.0 | 13.0 | 0.0 | 0.0 | 10.0 | 10.0 | 0.0 | 0.0 | 110.0 | 110.0 | 0.0 | 0.0 | 1245.35 | 1251.51 | 6.16 | 0.49 | 97.65 | 88.69 | -8.96 | -9.17 | 628.09 | 596.5 | -31.59 | -5.03 | 95.63 | 90.38 | -5.25 | -5.49 | 2303.0 | 2328.0 | 25.0 | 1.09 | 2618.95 | 2554.68 | -64.27 | -2.45 |
| 100 | 13.0 | 13.0 | 0.0 | 0.0 | 10.0 | 10.0 | 0.0 | 0.0 | 110.0 | 110.0 | 0.0 | 0.0 | 1258.95 | 1258.37 | -0.58 | -0.05 | 87.87 | 92.27 | 4.4 | 5.01 | 582.34 | 624.46 | 42.12 | 7.23 | 87.29 | 93.93 | 6.64 | 7.6 | 2333.0 | 2338.0 | 5.0 | 0.21 | 2609.65 | 2578.97 | -30.68 | -1.18 |
| 125 | 12.0 | 12.0 | 0.0 | 0.0 | 10.0 | 10.0 | 0.0 | 0.0 | 110.0 | 110.0 | 0.0 | 0.0 | 1258.64 | 1259.06 | 0.42 | 0.03 | 95.79 | 104.95 | 9.16 | 9.56 | 640.82 | 756.48 | 115.66 | 18.05 | 95.23 | 107.05 | 11.82 | 12.42 | 2334.0 | 2347.0 | 13.0 | 0.56 | 2614.17 | 2567.96 | -46.22 | -1.77 |
| 192 | 12.0 | 13.0 | 1.0 | 8.33 | 10.0 | 10.0 | 0.0 | 0.0 | 110.0 | 110.0 | 0.0 | 0.0 | 1257.8 | 1256.21 | -1.59 | -0.13 | 95.05 | 89.49 | -5.57 | -5.86 | 624.94 | 599.52 | -25.42 | -4.07 | 93.43 | 89.89 | -3.54 | -3.79 | 2322.0 | 2337.0 | 15.0 | 0.65 | 2627.34 | 2556.37 | -70.98 | -2.7 |
| 200 | 12.0 | 12.0 | 0.0 | 0.0 | 10.0 | 10.0 | 0.0 | 0.0 | 110.0 | 110.0 | 0.0 | 0.0 | 1250.23 | 1252.36 | 2.12 | 0.17 | 99.23 | 103.67 | 4.44 | 4.48 | 669.1 | 704.21 | 35.11 | 5.25 | 97.32 | 103.97 | 6.65 | 6.84 | 2313.0 | 2326.0 | 13.0 | 0.56 | 2609.53 | 2546.9 | -62.64 | -2.4 |
| 250 | 12.0 | 13.0 | 1.0 | 8.33 | 10.0 | 10.0 | 0.0 | 0.0 | 110.0 | 110.0 | 0.0 | 0.0 | 1247.76 | 1250.29 | 2.53 | 0.2 | 118.14 | 111.18 | -6.96 | -5.89 | 696.24 | 588.52 | -107.73 | -15.47 | 102.45 | 97.26 | -5.19 | -5.07 | 2307.0 | 2317.0 | 10.0 | 0.43 | 6102.32 | 4974.73 | -1127.58 | -18.48 |
| 256 | 12.0 | 12.0 | 0.0 | 0.0 | 10.0 | 10.0 | 0.0 | 0.0 | 110.0 | 110.0 | 0.0 | 0.0 | 1254.09 | 1257.54 | 3.45 | 0.28 | 151.14 | 132.61 | -18.54 | -12.26 | 771.42 | 718.83 | -52.59 | -6.82 | 114.01 | 108.97 | -5.04 | -4.42 | 2327.0 | 2342.0 | 15.0 | 0.64 | 7119.38 | 5721.63 | -1397.75 | -19.63 |

The within-PWM-step standard deviation is the primary short-term variability measure. It is calculated from samples inside each 10-second PWM interval; full-run speed spread is not used as a noise estimate.

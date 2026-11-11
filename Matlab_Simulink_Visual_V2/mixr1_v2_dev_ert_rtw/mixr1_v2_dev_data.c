/*
 * mixr1_v2_dev_data.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "mixr1_v2_dev".
 *
 * Model version              : 1.31
 * Simulink Coder version : 26.1 (R2026a) 20-Nov-2025
 * C source code generated on : Wed Nov 11 23:40:37 2026
 *
 * Target selection: ert.tlc
 * Embedded hardware selection: ARM Compatible->ARM Cortex-A (64-bit)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "mixr1_v2_dev.h"

/* Block parameters (default storage) */
P_mixr1_v2_dev_T mixr1_v2_dev_P = {
  /* Expression: mixr1_bench.tof_offset_mm
   * Referenced by: '<S2>/mixr1_bench.tof_offset_mm'
   */
  -26.0,

  /* Expression: mixr1_bench.tof_budget_ms
   * Referenced by: '<S2>/mixr1_bench.tof_budget_ms'
   */
  200.0,

  /* Expression: mixr1_bench.tof_gain
   * Referenced by: '<S2>/gain'
   */
  1.00901,

  /* Expression: mixr1_bench.tof_intercept
   * Referenced by: '<S2>/intercept'
   */
  14.477,

  /* Expression: mixr1_bench.zero_mm
   * Referenced by: '<S2>/zero'
   */
  389.0,

  /* Expression: mixr1_bench.thickness_mm
   * Referenced by: '<S2>/thickness'
   */
  1.0,

  /* Expression: mixr1_bench.lgain
   * Referenced by: '<S2>/lgain'
   */
  1.0,

  /* Expression: 6
   * Referenced by: '<Root>/pumpV'
   */
  6.0,

  /* Expression: 6
   * Referenced by: '<Root>/valveV'
   */
  6.0,

  /* Expression: mixr1_bench.min_V
   * Referenced by: '<S1>/mixr1_bench.min_V'
   */
  6.0,

  /* Expression: mixr1_bench.max_V
   * Referenced by: '<S1>/mixr1_bench.max_V'
   */
  12.0,

  /* Expression: mixr1_bench.min_band_mm
   * Referenced by: '<S1>/mixr1_bench.min_band_mm'
   */
  2.0,

  /* Expression: 20
   * Referenced by: '<S1>/mixr1_bench.valve_floor_mm'
   */
  20.0,

  /* Expression: mixr1_bench.max_level_mm
   * Referenced by: '<S1>/mixr1_bench.max_level_mm'
   */
  300.0,

  /* Expression: mixr1_bench.ceiling_margin_mm
   * Referenced by: '<S1>/mixr1_bench.ceiling_margin_mm'
   */
  40.0,

  /* Expression: mixr1_bench.min_V
   * Referenced by: '<S4>/mixr1_bench.min_V'
   */
  6.0,

  /* Expression: mixr1_bench.max_V
   * Referenced by: '<S4>/mixr1_bench.max_V'
   */
  12.0,

  /* Expression: mixr1_bench.max_level_mm - mixr1_bench.ceiling_margin_mm
   * Referenced by: '<S4>/mixr1_bench.max_level_mm - mixr1_bench.ceiling_margin_mm'
   */
  260.0,

  /* Expression: mixr1_bench.max_run_s
   * Referenced by: '<S4>/mixr1_bench.max_run_s'
   */
  1800.0,

  /* Expression: mixr1_bench.min_V
   * Referenced by: '<S5>/mixr1_bench.min_V'
   */
  6.0,

  /* Expression: mixr1_bench.max_V
   * Referenced by: '<S5>/mixr1_bench.max_V'
   */
  12.0,

  /* Expression: mixr1_bench.max_level_mm - mixr1_bench.ceiling_margin_mm
   * Referenced by: '<S5>/mixr1_bench.max_level_mm - mixr1_bench.ceiling_margin_mm'
   */
  260.0,

  /* Expression: mixr1_bench.max_run_s
   * Referenced by: '<S5>/mixr1_bench.max_run_s'
   */
  1800.0,

  /* Expression: mixr1_bench.pump_on_counts
   * Referenced by: '<Root>/mixr1_bench.pump_on_counts'
   */
  149.0,

  /* Expression: mixr1_bench.valve_on_counts
   * Referenced by: '<Root>/mixr1_bench.valve_on_counts'
   */
  192.0
};

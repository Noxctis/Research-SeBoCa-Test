/*
 * mixr1_level_private.h
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "mixr1_level".
 *
 * Model version              : 1.10
 * Simulink Coder version : 26.1 (R2026a) 20-Nov-2025
 * C source code generated on : Tue Oct 27 13:53:17 2026
 *
 * Target selection: ert.tlc
 * Embedded hardware selection: ARM Compatible->ARM Cortex-A (64-bit)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#ifndef mixr1_level_private_h_
#define mixr1_level_private_h_
#include "rtwtypes.h"
#include "multiword_types.h"
#include "mixr1_level_types.h"

/* Private macros used by the generated code to access rtModel */
#ifndef rtmSetTFinal
#define rtmSetTFinal(rtm, val)         ((rtm)->Timing.tFinal = (val))
#endif

extern real_T rt_roundd_snf(real_T u);

#endif                                 /* mixr1_level_private_h_ */

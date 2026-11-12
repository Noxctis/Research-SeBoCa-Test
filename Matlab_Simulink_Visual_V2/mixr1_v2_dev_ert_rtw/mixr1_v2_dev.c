/*
 * mixr1_v2_dev.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "mixr1_v2_dev".
 *
 * Model version              : 1.35
 * Simulink Coder version : 26.1 (R2026a) 20-Nov-2025
 * C source code generated on : Thu Nov 12 18:50:48 2026
 *
 * Target selection: ert.tlc
 * Embedded hardware selection: ARM Compatible->ARM Cortex-A (64-bit)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "mixr1_v2_dev.h"
#include "tof_wrapper.h"
#include "act2_wrapper.h"
#include "rt_nonfinite.h"
#include "mixr1_v2_dev_private.h"
#include "rtwtypes.h"
#include <string.h>
#include <math.h>

/* Exported block parameters */
real_T student_band = 6.5942858014787946;/* Variable: student_band
                                          * Referenced by: '<Root>/band'
                                          */
real_T student_mode = 0.0;             /* Variable: student_mode
                                        * Referenced by: '<Root>/mode'
                                        */
real_T student_pumpV = 9.0;            /* Variable: student_pumpV
                                        * Referenced by: '<Root>/pumpV'
                                        */
real_T student_sp = 100.0;             /* Variable: student_sp
                                        * Referenced by: '<Root>/setpoint'
                                        */

/* Block signals (default storage) */
B_mixr1_v2_dev_T mixr1_v2_dev_B;

/* Continuous states */
X_mixr1_v2_dev_T mixr1_v2_dev_X;

/* Disabled State Vector */
XDis_mixr1_v2_dev_T mixr1_v2_dev_XDis;

/* Block states (default storage) */
DW_mixr1_v2_dev_T mixr1_v2_dev_DW;

/* Real-time model */
static RT_MODEL_mixr1_v2_dev_T mixr1_v2_dev_M_;
RT_MODEL_mixr1_v2_dev_T *const mixr1_v2_dev_M = &mixr1_v2_dev_M_;

/*
 * This function updates continuous states using the ODE3 fixed-step
 * solver algorithm
 */
static void rt_ertODEUpdateContinuousStates(RTWSolverInfo *si )
{
  /* Solver Matrices */
  static const real_T rt_ODE3_A[3] = {
    1.0/2.0, 3.0/4.0, 1.0
  };

  static const real_T rt_ODE3_B[3][3] = {
    { 1.0/2.0, 0.0, 0.0 },

    { 0.0, 3.0/4.0, 0.0 },

    { 2.0/9.0, 1.0/3.0, 4.0/9.0 }
  };

  time_T t = rtsiGetT(si);
  time_T tnew = rtsiGetSolverStopTime(si);
  time_T h = rtsiGetStepSize(si);
  real_T *x = rtsiGetContStates(si);
  ODE3_IntgData *id = (ODE3_IntgData *)rtsiGetSolverData(si);
  real_T *y = id->y;
  real_T *f0 = id->f[0];
  real_T *f1 = id->f[1];
  real_T *f2 = id->f[2];
  real_T hB[3];
  int_T i;
  int_T nXc = 1;
  rtsiSetSimTimeStep(si,MINOR_TIME_STEP);

  /* Save the state values at time t in y, we'll use x as ynew. */
  (void) memcpy(y, x,
                (uint_T)nXc*sizeof(real_T));

  /* Assumes that rtsiSetT and ModelOutputs are up-to-date */
  /* f0 = f(t,y) */
  rtsiSetdX(si, f0);
  mixr1_v2_dev_derivatives();

  /* f(:,2) = feval(odefile, t + hA(1), y + f*hB(:,1), args(:)(*)); */
  hB[0] = h * rt_ODE3_B[0][0];
  for (i = 0; i < nXc; i++) {
    x[i] = y[i] + (f0[i]*hB[0]);
  }

  rtsiSetT(si, t + h*rt_ODE3_A[0]);
  rtsiSetdX(si, f1);
  mixr1_v2_dev_step();
  mixr1_v2_dev_derivatives();

  /* f(:,3) = feval(odefile, t + hA(2), y + f*hB(:,2), args(:)(*)); */
  for (i = 0; i <= 1; i++) {
    hB[i] = h * rt_ODE3_B[1][i];
  }

  for (i = 0; i < nXc; i++) {
    x[i] = y[i] + (f0[i]*hB[0] + f1[i]*hB[1]);
  }

  rtsiSetT(si, t + h*rt_ODE3_A[1]);
  rtsiSetdX(si, f2);
  mixr1_v2_dev_step();
  mixr1_v2_dev_derivatives();

  /* tnew = t + hA(3);
     ynew = y + f*hB(:,3); */
  for (i = 0; i <= 2; i++) {
    hB[i] = h * rt_ODE3_B[2][i];
  }

  for (i = 0; i < nXc; i++) {
    x[i] = y[i] + (f0[i]*hB[0] + f1[i]*hB[1] + f2[i]*hB[2]);
  }

  rtsiSetT(si, tnew);
  rtsiSetSimTimeStep(si,MAJOR_TIME_STEP);
}

real_T rt_roundd_snf(real_T u)
{
  real_T y;
  if (fabs(u) < 4.503599627370496E+15) {
    if (u >= 0.5) {
      y = floor(u + 0.5);
    } else if (u > -0.5) {
      y = u * 0.0;
    } else {
      y = ceil(u - 0.5);
    }
  } else {
    y = u;
  }

  return y;
}

/* Model step function */
void mixr1_v2_dev_step(void)
{
  real_T d;
  real_T sp1;
  real_T trip;
  real_T valve_V;
  int32_T j2;
  int16_T tmp;
  uint16_T tmp_0;
  uint8_T guard;
  boolean_T active;
  boolean_T sees;
  boolean_T wanted;
  static const real_T b[14] = { 0.0, 1.92, 3.2, 4.1, 4.9, 5.7, 6.5, 7.2, 7.9,
    8.7, 9.4, 10.2, 10.9, 12.0 };

  static const uint8_T c[14] = { 0U, 12U, 25U, 37U, 50U, 62U, 75U, 87U, 99U,
    112U, 124U, 137U, 149U, 167U };

  boolean_T exitg1;
  if (rtmIsMajorTimeStep(mixr1_v2_dev_M)) {
    /* set solver stop time */
    rtsiSetSolverStopTime(&mixr1_v2_dev_M->solverInfo,
                          ((mixr1_v2_dev_M->Timing.clockTick0+1)*
      mixr1_v2_dev_M->Timing.stepSize0));
  }                                    /* end MajorTimeStep */

  /* Update absolute time of base rate at minor time step */
  if (rtmIsMinorTimeStep(mixr1_v2_dev_M)) {
    mixr1_v2_dev_M->Timing.t[0] = rtsiGetT(&mixr1_v2_dev_M->solverInfo);
  }

  wanted = rtmIsMajorTimeStep(mixr1_v2_dev_M);
  if (wanted) {
    /* MATLAB Function: '<S2>/tof_read' incorporates:
     *  Constant: '<S2>/mixr1_bench.tof_budget_ms'
     *  Constant: '<S2>/mixr1_bench.tof_offset_mm'
     */
    /* MATLAB Function 'Level Sensor/tof_read': '<S8>:1' */
    /* '<S8>:1:4' coder.extrinsic('which', 'fileparts'); */
    /* '<S8>:1:5' dist    = uint16(0); */
    /* '<S8>:1:6' status  = uint8(255); */
    /* '<S8>:1:7' newData = uint8(0); */
    /* '<S8>:1:10' if isempty(k) */
    /* '<S8>:1:17' if coder.target('Sfun') */
    /* '<S8>:1:32' else */
    /* '<S8>:1:33' srcDir = coder.const(fileparts(which('tof_wrapper.c'))); */
    /* '<S8>:1:34' coder.cinclude('tof_wrapper.h'); */
    /* '<S8>:1:35' coder.updateBuildInfo('addIncludePaths', srcDir); */
    /* '<S8>:1:36' coder.updateBuildInfo('addSourcePaths',  srcDir); */
    /* '<S8>:1:37' coder.updateBuildInfo('addSourceFiles', 'tof_wrapper.c'); */
    /* '<S8>:1:38' coder.updateBuildInfo('addSourceFiles', 'VL53L4CD_api.c'); */
    /* '<S8>:1:39' coder.updateBuildInfo('addSourceFiles', 'platform.c'); */
    /* '<S8>:1:41' if ~started */
    if (!mixr1_v2_dev_DW.started_d) {
      /* '<S8>:1:42' coder.ceval('tof_init', int16(offset_mm), uint16(budget_ms)); */
      trip = rt_roundd_snf(mixr1_v2_dev_P.mixr1_benchtof_offset_mm_Value);
      d = rt_roundd_snf(mixr1_v2_dev_P.mixr1_benchtof_budget_ms_Value);
      if (trip < 32768.0) {
        if (trip >= -32768.0) {
          tmp = (int16_T)trip;
        } else {
          tmp = MIN_int16_T;
        }
      } else {
        tmp = MAX_int16_T;
      }

      if (d < 65536.0) {
        if (d >= 0.0) {
          tmp_0 = (uint16_T)d;
        } else {
          tmp_0 = 0U;
        }
      } else {
        tmp_0 = MAX_uint16_T;
      }

      tof_init(tmp, tmp_0);

      /* '<S8>:1:43' started = true; */
      mixr1_v2_dev_DW.started_d = true;
    }

    /* '<S8>:1:45' coder.ceval('tof_step', coder.wref(dist), coder.wref(status), coder.wref(newData)); */
    tof_step(&mixr1_v2_dev_B.dist, &mixr1_v2_dev_B.status,
             &mixr1_v2_dev_B.newData);

    /* End of MATLAB Function: '<S2>/tof_read' */

    /* MATLAB Function: '<S2>/level_calc' incorporates:
     *  Constant: '<S2>/gain'
     *  Constant: '<S2>/intercept'
     *  Constant: '<S2>/lgain'
     *  Constant: '<S2>/thickness'
     *  Constant: '<S2>/zero'
     */
    /* MATLAB Function 'Level Sensor/level_calc': '<S7>:1' */
    /* '<S7>:1:8' MAX_AGE = 12; */
    /* '<S7>:1:11' if isempty(buf) */
    /* '<S7>:1:16' newOut = (newData == 1); */
    mixr1_v2_dev_B.newOut = (mixr1_v2_dev_B.newData == 1);

    /* '<S7>:1:17' if newData == 1 */
    if (mixr1_v2_dev_B.newData == 1) {
      /* '<S7>:1:18' d = (double(dist) - intercept) / gain; */
      d = ((real_T)mixr1_v2_dev_B.dist - mixr1_v2_dev_P.intercept_Value) /
        mixr1_v2_dev_P.gain_Value;

      /* '<S7>:1:19' if status == 0 && d > 30 && d <= 2000 */
      if ((mixr1_v2_dev_B.status == 0) && (d > 30.0) && (d <= 2000.0)) {
        /* '<S7>:1:20' if age > MAX_AGE */
        if (mixr1_v2_dev_DW.age > 12.0) {
          /* '<S7>:1:20' , */
          /* '<S7>:1:20' n = 0; */
          mixr1_v2_dev_DW.n = 0.0;
        }

        /* '<S7>:1:21' buf  = [buf(2:3), d]; */
        mixr1_v2_dev_DW.buf[0] = mixr1_v2_dev_DW.buf[1];
        mixr1_v2_dev_DW.buf[1] = mixr1_v2_dev_DW.buf[2];
        mixr1_v2_dev_DW.buf[2] = d;

        /* '<S7>:1:22' n    = min(n + 1, 3); */
        if (mixr1_v2_dev_DW.n + 1.0 <= 3.0) {
          mixr1_v2_dev_DW.n++;
        } else {
          mixr1_v2_dev_DW.n = 3.0;
        }

        /* '<S7>:1:23' age  = 0; */
        mixr1_v2_dev_DW.age = 0.0;

        /* '<S7>:1:24' have = true; */
        mixr1_v2_dev_DW.have = true;

        /* '<S7>:1:25' rawV = double(dist); */
        /* '<S7>:1:26' corrV = d; */
        /* '<S7>:1:27' lvl  = max(0, lgain * (zero - median(buf(4-n:3)) - thickness)); */
        switch (4 - (int32_T)(4.0 - mixr1_v2_dev_DW.n)) {
         case 1:
          d = mixr1_v2_dev_DW.buf[(int32_T)(4.0 - mixr1_v2_dev_DW.n) - 1];
          break;

         case 2:
          d = mixr1_v2_dev_DW.buf[(int32_T)(4.0 - mixr1_v2_dev_DW.n) - 1];
          d += (mixr1_v2_dev_DW.buf[(int32_T)(4.0 - mixr1_v2_dev_DW.n)] - d) /
            2.0;
          break;

         default:
          trip = mixr1_v2_dev_DW.buf[(int32_T)(4.0 - mixr1_v2_dev_DW.n) - 1];
          d = mixr1_v2_dev_DW.buf[(int32_T)(4.0 - mixr1_v2_dev_DW.n)];
          if (trip < d) {
            if (d < mixr1_v2_dev_DW.buf[(int32_T)(4.0 - mixr1_v2_dev_DW.n) + 1])
            {
              j2 = 1;
            } else if (trip < mixr1_v2_dev_DW.buf[(int32_T)(4.0 -
                        mixr1_v2_dev_DW.n) + 1]) {
              j2 = 2;
            } else {
              j2 = 0;
            }
          } else if (trip < mixr1_v2_dev_DW.buf[(int32_T)(4.0 -
                      mixr1_v2_dev_DW.n) + 1]) {
            j2 = 0;
          } else if (d < mixr1_v2_dev_DW.buf[(int32_T)(4.0 - mixr1_v2_dev_DW.n)
                     + 1]) {
            j2 = 2;
          } else {
            j2 = 1;
          }

          d = mixr1_v2_dev_DW.buf[((int32_T)(4.0 - mixr1_v2_dev_DW.n) + j2) - 1];
          break;
        }

        valve_V = ((mixr1_v2_dev_P.zero_Value - d) -
                   mixr1_v2_dev_P.thickness_Value) * mixr1_v2_dev_P.lgain_Value;
        if ((valve_V <= 0.0) || rtIsNaN(valve_V)) {
          mixr1_v2_dev_DW.lvl = 0.0;
        } else {
          mixr1_v2_dev_DW.lvl = valve_V;
        }

        /* '<S7>:1:28' else */
        /* '<S7>:1:29' age = min(age + 1, 1e6); */
      } else if (mixr1_v2_dev_DW.age + 1.0 <= 1.0E+6) {
        mixr1_v2_dev_DW.age++;
      } else {
        mixr1_v2_dev_DW.age = 1.0E+6;
      }

      /* '<S7>:1:31' else */
      /* '<S7>:1:32' age = min(age + 1, 1e6); */
    } else if (mixr1_v2_dev_DW.age + 1.0 <= 1.0E+6) {
      mixr1_v2_dev_DW.age++;
    } else {
      mixr1_v2_dev_DW.age = 1.0E+6;
    }

    /* '<S7>:1:35' level = lvl; */
    mixr1_v2_dev_B.level = mixr1_v2_dev_DW.lvl;

    /* '<S7>:1:36' valid = have && (age <= MAX_AGE); */
    mixr1_v2_dev_B.valid = (mixr1_v2_dev_DW.have && (mixr1_v2_dev_DW.age <= 12.0));

    /* End of MATLAB Function: '<S2>/level_calc' */

    /* Scope: '<Root>/Scope' */
    /* '<S7>:1:37' raw   = rawV; */
    /* '<S7>:1:38' corr  = corrV; */
  }

  /* TransferFcn: '<Root>/level_display (smoothed, display only — not used for control).' */
  mixr1_v2_dev_B.level_displaysmootheddisplayonl = 0.0;
  mixr1_v2_dev_B.level_displaysmootheddisplayonl +=
    mixr1_v2_dev_P.level_displaysmootheddisplayo_c *
    mixr1_v2_dev_X.level_displaysmootheddisplayonl;
  if (wanted) {
    /* MATLAB Function: '<S1>/MATLAB Function' incorporates:
     *  Constant: '<Root>/band'
     *  Constant: '<Root>/mode'
     *  Constant: '<Root>/pumpV'
     *  Constant: '<Root>/setpoint'
     *  Constant: '<S1>/mixr1_bench.ceiling_margin_mm'
     *  Constant: '<S1>/mixr1_bench.max_V'
     *  Constant: '<S1>/mixr1_bench.max_level_mm'
     *  Constant: '<S1>/mixr1_bench.min_V'
     *  Constant: '<S1>/mixr1_bench.min_band_mm'
     *  Constant: '<S1>/mixr1_bench.valve_floor_mm'
     *  Constant: '<S1>/valveV'
     */
    /* MATLAB Function 'Controller/MATLAB Function': '<S6>:1' */
    /* '<S6>:1:17' if isempty(sw) */
    /* '<S6>:1:19' trip      = max_level - margin; */
    trip = mixr1_v2_dev_P.mixr1_benchmax_level_mm_Value -
      mixr1_v2_dev_P.mixr1_benchceiling_margin_mm_Va;

    /* '<S6>:1:20' p         = min(max(band_pct, 0), 50) / 100; */
    if (student_band >= 0.0) {
      d = student_band;
    } else {
      d = 0.0;
    }

    if (!(d <= 50.0)) {
      d = 50.0;
    }

    d /= 100.0;

    /* '<S6>:1:21' sp1       = min(setpoint, trip / (1 + p)); */
    sp1 = trip / (d + 1.0);
    if ((student_sp <= sp1) || rtIsNaN(sp1)) {
      sp1 = student_sp;
    }

    /* '<S6>:1:22' band_used = min(max(sp1 * p, min_band), (trip - floor_mm) / 2); */
    valve_V = sp1 * d;
    if (!(valve_V >= mixr1_v2_dev_P.mixr1_benchmin_band_mm_Value) && !rtIsNaN
        (mixr1_v2_dev_P.mixr1_benchmin_band_mm_Value)) {
      valve_V = mixr1_v2_dev_P.mixr1_benchmin_band_mm_Value;
    }

    d = (trip - mixr1_v2_dev_P.mixr1_benchvalve_floor_mm_Value) / 2.0;
    if ((valve_V <= d) || rtIsNaN(d)) {
      d = valve_V;
    }

    /* '<S6>:1:23' sp_used   = min(max(sp1, floor_mm + band_used), trip - band_used); */
    valve_V = mixr1_v2_dev_P.mixr1_benchvalve_floor_mm_Value + d;
    if ((sp1 >= valve_V) || rtIsNaN(valve_V)) {
      valve_V = sp1;
    }

    trip -= d;
    if ((valve_V <= trip) || rtIsNaN(trip)) {
      trip = valve_V;
    }

    /* '<S6>:1:24' pump_V    = min(max(pumpV,  min_V), max_V); */
    active = rtIsNaN(mixr1_v2_dev_P.mixr1_benchmin_V_Value);
    if ((student_pumpV >= mixr1_v2_dev_P.mixr1_benchmin_V_Value) || active) {
      sp1 = student_pumpV;
    } else {
      sp1 = mixr1_v2_dev_P.mixr1_benchmin_V_Value;
    }

    wanted = !rtIsNaN(mixr1_v2_dev_P.mixr1_benchmax_V_Value);
    if (!(sp1 <= mixr1_v2_dev_P.mixr1_benchmax_V_Value) && wanted) {
      sp1 = mixr1_v2_dev_P.mixr1_benchmax_V_Value;
    }

    /* '<S6>:1:25' valve_V   = min(max(valveV, min_V), max_V); */
    if ((mixr1_v2_dev_P.valveV_Value >= mixr1_v2_dev_P.mixr1_benchmin_V_Value) ||
        active) {
      valve_V = mixr1_v2_dev_P.valveV_Value;
    } else {
      valve_V = mixr1_v2_dev_P.mixr1_benchmin_V_Value;
    }

    if (!(valve_V <= mixr1_v2_dev_P.mixr1_benchmax_V_Value) && wanted) {
      valve_V = mixr1_v2_dev_P.mixr1_benchmax_V_Value;
    }

    /* '<S6>:1:27' if mode ~= prevMode */
    if (student_mode != mixr1_v2_dev_DW.prevMode) {
      /* '<S6>:1:27' , */
      /* '<S6>:1:27' sw = false; */
      mixr1_v2_dev_DW.sw = false;
    }

    /* '<S6>:1:28' prevMode = mode; */
    mixr1_v2_dev_DW.prevMode = student_mode;

    /* '<S6>:1:30' if mode == 0 */
    if (student_mode == 0.0) {
      /* '<S6>:1:30' , */
      /* '<S6>:1:30' armed = true; */
      mixr1_v2_dev_DW.armed = true;
    }

    /* '<S6>:1:31' wanted  = (mode == 1 || mode == 2 || mode == 3); */
    wanted = ((student_mode == 1.0) || (student_mode == 2.0) || (student_mode ==
               3.0));

    /* '<S6>:1:32' active  = armed && wanted; */
    active = (mixr1_v2_dev_DW.armed && wanted);

    /* '<S6>:1:33' pump_en = false; */
    mixr1_v2_dev_B.pump_en = false;

    /* '<S6>:1:34' valve_en = false; */
    mixr1_v2_dev_B.valve_en = false;

    /* '<S6>:1:35' status  = uint8(0); */
    mixr1_v2_dev_B.status_p = 0U;

    /* '<S6>:1:37' if ~active || ~valid */
    if (!active || !mixr1_v2_dev_B.valid) {
      /* '<S6>:1:38' sw = false; */
      mixr1_v2_dev_DW.sw = false;

      /* '<S6>:1:39' if active */
      if (active) {
        /* '<S6>:1:40' status = uint8(3); */
        mixr1_v2_dev_B.status_p = 3U;
      } else if (wanted) {
        /* '<S6>:1:41' elseif wanted */
        /* '<S6>:1:42' status = uint8(4); */
        mixr1_v2_dev_B.status_p = 4U;
      }
    } else if (student_mode == 3.0) {
      /* '<S6>:1:44' elseif mode == 3 */
      /* '<S6>:1:45' sw       = false; */
      mixr1_v2_dev_DW.sw = false;

      /* '<S6>:1:46' pump_en  = false; */
      mixr1_v2_dev_B.pump_en = false;

      /* '<S6>:1:47' valve_en = true; */
      mixr1_v2_dev_B.valve_en = true;

      /* '<S6>:1:48' status   = uint8(2); */
      mixr1_v2_dev_B.status_p = 2U;
    } else if (student_mode == 1.0) {
      /* '<S6>:1:49' elseif mode == 1 */
      /* '<S6>:1:50' if level >= sp_used + band_used */
      if (mixr1_v2_dev_B.level >= trip + d) {
        /* '<S6>:1:51' sw = true; */
        mixr1_v2_dev_DW.sw = true;
      } else if (mixr1_v2_dev_B.level <= trip - d) {
        /* '<S6>:1:52' elseif level <= sp_used - band_used */
        /* '<S6>:1:53' sw = false; */
        mixr1_v2_dev_DW.sw = false;
      }

      /* '<S6>:1:55' pump_en  = true; */
      mixr1_v2_dev_B.pump_en = true;

      /* '<S6>:1:56' valve_en = sw; */
      mixr1_v2_dev_B.valve_en = mixr1_v2_dev_DW.sw;

      /* '<S6>:1:57' status   = uint8(1 + double(sw)); */
      mixr1_v2_dev_B.status_p = (uint8_T)(mixr1_v2_dev_DW.sw + 1);
    } else {
      /* '<S6>:1:58' else */
      /* '<S6>:1:59' if level <= sp_used - band_used */
      if (mixr1_v2_dev_B.level <= trip - d) {
        /* '<S6>:1:60' sw = true; */
        mixr1_v2_dev_DW.sw = true;
      } else if (mixr1_v2_dev_B.level >= trip + d) {
        /* '<S6>:1:61' elseif level >= sp_used + band_used */
        /* '<S6>:1:62' sw = false; */
        mixr1_v2_dev_DW.sw = false;
      }

      /* '<S6>:1:64' pump_en  = sw; */
      mixr1_v2_dev_B.pump_en = mixr1_v2_dev_DW.sw;

      /* '<S6>:1:65' valve_en = true; */
      mixr1_v2_dev_B.valve_en = true;

      /* '<S6>:1:66' status   = uint8(2 - double(sw)); */
      mixr1_v2_dev_B.status_p = (uint8_T)(2 - mixr1_v2_dev_DW.sw);
    }

    /* End of MATLAB Function: '<S1>/MATLAB Function' */
    /* MATLAB Function: '<S4>/pump_guard' incorporates:
     *  Constant: '<S4>/mixr1_bench.max_V'
     *  Constant: '<S4>/mixr1_bench.max_level_mm - mixr1_bench.ceiling_margin_mm'
     *  Constant: '<S4>/mixr1_bench.max_run_s'
     *  Constant: '<S4>/mixr1_bench.min_V'
     *  MATLAB Function: '<S5>/valve_guard'
     */
    /* MATLAB Function 'Pump Guard/pump_guard': '<S9>:1' */
    /* '<S9>:1:8' DT = 0.05; */
    /* '<S9>:1:8' RELEASE = 5; */
    /* '<S9>:1:8' REST_S = 2; */
    /* '<S9>:1:10' if isempty(atCeiling) */
    /* '<S9>:1:14' want  = enable && cmd > 0; */
    wanted = (mixr1_v2_dev_B.pump_en && (sp1 > 0.0));

    /* '<S9>:1:15' sees  = valid && isfinite(level); */
    sees = (mixr1_v2_dev_B.valid && (!rtIsInf(mixr1_v2_dev_B.level) && !rtIsNaN
             (mixr1_v2_dev_B.level)));

    /* '<S9>:1:17' if sees */
    if (sees) {
      /* '<S9>:1:18' if level >= trip */
      if (mixr1_v2_dev_B.level >= mixr1_v2_dev_P.mixr1_benchmax_level_mmmixr1_be)
      {
        /* '<S9>:1:19' atCeiling = true; */
        mixr1_v2_dev_DW.atCeiling = true;
      } else if (mixr1_v2_dev_B.level <=
                 mixr1_v2_dev_P.mixr1_benchmax_level_mmmixr1_be - 5.0) {
        /* '<S9>:1:20' elseif level <= trip - RELEASE */
        /* '<S9>:1:21' atCeiling = false; */
        mixr1_v2_dev_DW.atCeiling = false;
      }
    }

    /* '<S9>:1:25' if want */
    if (wanted) {
      /* '<S9>:1:26' offSteps = 0; */
      mixr1_v2_dev_DW.offSteps_m = 0.0;
    } else {
      /* '<S9>:1:27' else */
      /* '<S9>:1:28' offSteps = min(offSteps + 1, 1e6); */
      if (mixr1_v2_dev_DW.offSteps_m + 1.0 <= 1.0E+6) {
        mixr1_v2_dev_DW.offSteps_m++;
      } else {
        mixr1_v2_dev_DW.offSteps_m = 1.0E+6;
      }

      /* '<S9>:1:29' if offSteps * DT >= REST_S */
      if (mixr1_v2_dev_DW.offSteps_m * 0.05 >= 2.0) {
        /* '<S9>:1:30' runSteps = 0; */
        mixr1_v2_dev_DW.runSteps_g = 0.0;

        /* '<S9>:1:31' latched  = false; */
        mixr1_v2_dev_DW.latched_e = false;
      }
    }

    /* '<S9>:1:35' if ~sees */
    active = !sees;
    if (active) {
      /* '<S9>:1:36' guard = uint8(1); */
      guard = 1U;
    } else if (mixr1_v2_dev_DW.atCeiling) {
      /* '<S9>:1:37' elseif atCeiling */
      /* '<S9>:1:38' guard = uint8(3); */
      guard = 3U;
    } else if (mixr1_v2_dev_DW.latched_e) {
      /* '<S9>:1:39' elseif latched */
      /* '<S9>:1:40' guard = uint8(4); */
      guard = 4U;
    } else {
      /* '<S9>:1:41' else */
      /* '<S9>:1:42' guard = uint8(0); */
      guard = 0U;
    }

    /* '<S9>:1:45' if want && guard == 0 */
    if (wanted && (guard == 0)) {
      /* '<S9>:1:46' runSteps = runSteps + 1; */
      mixr1_v2_dev_DW.runSteps_g++;

      /* '<S9>:1:47' if runSteps * DT >= max_run_s */
      if (mixr1_v2_dev_DW.runSteps_g * 0.05 >=
          mixr1_v2_dev_P.mixr1_benchmax_run_s_Value) {
        /* '<S9>:1:48' latched = true; */
        mixr1_v2_dev_DW.latched_e = true;

        /* '<S9>:1:49' guard   = uint8(4); */
        guard = 4U;
      }
    }

    /* '<S9>:1:53' applied_V = 0; */
    mixr1_v2_dev_B.applied_V_d = 0.0;

    /* '<S9>:1:54' if want && guard == 0 */
    if (wanted && (guard == 0)) {
      /* '<S9>:1:55' applied_V = min(max(cmd, min_V), max_V); */
      if (!(sp1 >= mixr1_v2_dev_P.mixr1_benchmin_V_Value_i) && !rtIsNaN
          (mixr1_v2_dev_P.mixr1_benchmin_V_Value_i)) {
        sp1 = mixr1_v2_dev_P.mixr1_benchmin_V_Value_i;
      }

      if ((sp1 <= mixr1_v2_dev_P.mixr1_benchmax_V_Value_c) || rtIsNaN
          (mixr1_v2_dev_P.mixr1_benchmax_V_Value_c)) {
        mixr1_v2_dev_B.applied_V_d = sp1;
      } else {
        mixr1_v2_dev_B.applied_V_d = mixr1_v2_dev_P.mixr1_benchmax_V_Value_c;
      }
    }

    mixr1_v2_dev_B.guard_b = guard;

    /* End of MATLAB Function: '<S4>/pump_guard' */
    /* MATLAB Function: '<S5>/valve_guard' incorporates:
     *  Constant: '<S5>/mixr1_bench.max_V'
     *  Constant: '<S5>/mixr1_bench.max_run_s'
     *  Constant: '<S5>/mixr1_bench.min_V'
     *  Constant: '<S5>/mixr1_bench.valve_floor_mm'
     */
    /* MATLAB Function 'Valve Guard/valve_guard': '<S10>:1' */
    /* '<S10>:1:7' DT = 0.05; */
    /* '<S10>:1:7' RELEASE = 2; */
    /* '<S10>:1:7' REST_S = 2; */
    /* '<S10>:1:9' if isempty(atFloor) */
    /* '<S10>:1:13' want = enable && cmd > 0; */
    wanted = (mixr1_v2_dev_B.valve_en && (valve_V > 0.0));

    /* '<S10>:1:14' sees = valid && isfinite(level); */
    /* '<S10>:1:16' if sees */
    if (sees) {
      /* '<S10>:1:17' if level <= floor_mm */
      if (mixr1_v2_dev_B.level <= mixr1_v2_dev_P.mixr1_benchvalve_floor_mm_Val_p)
      {
        /* '<S10>:1:18' atFloor = true; */
        mixr1_v2_dev_DW.atFloor = true;
      } else if (mixr1_v2_dev_B.level >=
                 mixr1_v2_dev_P.mixr1_benchvalve_floor_mm_Val_p + 2.0) {
        /* '<S10>:1:19' elseif level >= floor_mm + RELEASE */
        /* '<S10>:1:20' atFloor = false; */
        mixr1_v2_dev_DW.atFloor = false;
      }
    }

    /* '<S10>:1:24' if want */
    if (wanted) {
      /* '<S10>:1:25' offSteps = 0; */
      mixr1_v2_dev_DW.offSteps = 0.0;
    } else {
      /* '<S10>:1:26' else */
      /* '<S10>:1:27' offSteps = min(offSteps + 1, 1e6); */
      if (mixr1_v2_dev_DW.offSteps + 1.0 <= 1.0E+6) {
        mixr1_v2_dev_DW.offSteps++;
      } else {
        mixr1_v2_dev_DW.offSteps = 1.0E+6;
      }

      /* '<S10>:1:28' if offSteps * DT >= REST_S */
      if (mixr1_v2_dev_DW.offSteps * 0.05 >= 2.0) {
        /* '<S10>:1:29' runSteps = 0; */
        mixr1_v2_dev_DW.runSteps = 0.0;

        /* '<S10>:1:30' latched  = false; */
        mixr1_v2_dev_DW.latched = false;
      }
    }

    /* '<S10>:1:34' if ~sees */
    if (active) {
      /* '<S10>:1:35' guard = uint8(1); */
      guard = 1U;
    } else if (mixr1_v2_dev_DW.atFloor) {
      /* '<S10>:1:36' elseif atFloor */
      /* '<S10>:1:37' guard = uint8(5); */
      guard = 5U;
    } else if (mixr1_v2_dev_DW.latched) {
      /* '<S10>:1:38' elseif latched */
      /* '<S10>:1:39' guard = uint8(4); */
      guard = 4U;
    } else {
      /* '<S10>:1:40' else */
      /* '<S10>:1:41' guard = uint8(0); */
      guard = 0U;
    }

    /* '<S10>:1:44' if want && guard == 0 */
    if (wanted && (guard == 0)) {
      /* '<S10>:1:45' runSteps = runSteps + 1; */
      mixr1_v2_dev_DW.runSteps++;

      /* '<S10>:1:46' if runSteps * DT >= max_run_s */
      if (mixr1_v2_dev_DW.runSteps * 0.05 >=
          mixr1_v2_dev_P.mixr1_benchmax_run_s_Value_c) {
        /* '<S10>:1:47' latched = true; */
        mixr1_v2_dev_DW.latched = true;

        /* '<S10>:1:48' guard   = uint8(4); */
        guard = 4U;
      }
    }

    /* '<S10>:1:52' applied_V = 0; */
    mixr1_v2_dev_B.applied_V = 0.0;

    /* '<S10>:1:53' if want && guard == 0 */
    if (wanted && (guard == 0)) {
      /* '<S10>:1:54' applied_V = min(max(cmd, min_V), max_V); */
      if (!(valve_V >= mixr1_v2_dev_P.mixr1_benchmin_V_Value_a) && !rtIsNaN
          (mixr1_v2_dev_P.mixr1_benchmin_V_Value_a)) {
        valve_V = mixr1_v2_dev_P.mixr1_benchmin_V_Value_a;
      }

      if ((valve_V <= mixr1_v2_dev_P.mixr1_benchmax_V_Value_g) || rtIsNaN
          (mixr1_v2_dev_P.mixr1_benchmax_V_Value_g)) {
        mixr1_v2_dev_B.applied_V = valve_V;
      } else {
        mixr1_v2_dev_B.applied_V = mixr1_v2_dev_P.mixr1_benchmax_V_Value_g;
      }
    }

    mixr1_v2_dev_B.guard = guard;

    /* MATLAB Function: '<Root>/MATLAB Function' incorporates:
     *  Constant: '<Root>/mixr1_bench.pump_on_counts'
     *  Constant: '<Root>/mixr1_bench.valve_on_counts'
     */
    /* MATLAB Function 'MATLAB Function': '<S3>:1' */
    /* '<S3>:1:8' coder.extrinsic('which', 'fileparts'); */
    /* '<S3>:1:10' if isempty(started) */
    /* '<S3>:1:11' if ~coder.target('Sfun') */
    /* '<S3>:1:12' srcDir = coder.const(fileparts(which('act2_wrapper.c'))); */
    /* '<S3>:1:13' coder.cinclude('act2_wrapper.h'); */
    /* '<S3>:1:14' coder.updateBuildInfo('addIncludePaths', srcDir); */
    /* '<S3>:1:15' coder.updateBuildInfo('addSourcePaths',  srcDir); */
    /* '<S3>:1:16' coder.updateBuildInfo('addSourceFiles', 'act2_wrapper.c'); */
    /* '<S3>:1:17' coder.updateBuildInfo('addLinkFlags', '-lwiringPi'); */
    /* '<S3>:1:18' if ~started */
    if (!mixr1_v2_dev_DW.started) {
      /* '<S3>:1:19' coder.ceval('act2_init'); */
      act2_init();

      /* '<S3>:1:20' started = true; */
      mixr1_v2_dev_DW.started = true;
    }

    /* '<S3>:1:26' CAL_V = [0 1.92 3.2 4.1 4.9 5.7 6.5 7.2 7.9 8.7 9.4 10.2 10.9 12.0]; */
    /* '<S3>:1:27' CAL_C = [0 12 25 37 50 62 75 87 99 112 124 137 149 167]; */
    /* '<S3>:1:28' t  = double(pump_V); */
    /* '<S3>:1:29' pc = CAL_C(end); */
    d = 167.0;

    /* '<S3>:1:30' if t < CAL_V(end) */
    if (mixr1_v2_dev_B.applied_V_d < 12.0) {
      /* '<S3>:1:31' for k = 2:numel(CAL_V) */
      j2 = 0;
      exitg1 = false;
      while (!exitg1 && (j2 < 13)) {
        /* '<S3>:1:32' if t <= CAL_V(k) */
        trip = b[j2 + 1];
        if (mixr1_v2_dev_B.applied_V_d <= trip) {
          /* '<S3>:1:33' pc = CAL_C(k-1) + (CAL_C(k) - CAL_C(k-1)) * (t - CAL_V(k-1)) / (CAL_V(k) - CAL_V(k-1)); */
          d = (real_T)(c[j2 + 1] - c[j2]) * (mixr1_v2_dev_B.applied_V_d - b[j2])
            / (trip - b[j2]) + (real_T)c[j2];
          exitg1 = true;
        } else {
          j2++;
        }
      }
    }

    /* '<S3>:1:38' pc = min(pc, double(pump_counts)); */
    if (!(d <= mixr1_v2_dev_P.mixr1_benchpump_on_counts_Value) && !rtIsNaN
        (mixr1_v2_dev_P.mixr1_benchpump_on_counts_Value)) {
      d = mixr1_v2_dev_P.mixr1_benchpump_on_counts_Value;
    }

    /* '<S3>:1:39' if pump_V > 0 */
    if ((mixr1_v2_dev_B.applied_V_d > 0.0) && !(d >= 1.0)) {
      /* '<S3>:1:39' , */
      /* '<S3>:1:39' pc = max(pc, 1); */
      d = 1.0;
    }

    /* '<S3>:1:40' coder.ceval('act2_pump',  uint8(pump_V  > 0), uint16(round(pc))); */
    trip = rt_roundd_snf(d);
    if (trip < 65536.0) {
      if (trip >= 0.0) {
        tmp_0 = (uint16_T)trip;
      } else {
        tmp_0 = 0U;
      }
    } else {
      tmp_0 = MAX_uint16_T;
    }

    act2_pump((uint8_T)(mixr1_v2_dev_B.applied_V_d > 0.0), tmp_0);

    /* '<S3>:1:41' coder.ceval('act2_valve', uint8(valve_V > 0), uint16(valve_counts)); */
    trip = rt_roundd_snf(mixr1_v2_dev_P.mixr1_benchvalve_on_counts_Valu);
    if (trip < 65536.0) {
      if (trip >= 0.0) {
        tmp_0 = (uint16_T)trip;
      } else {
        tmp_0 = 0U;
      }
    } else {
      tmp_0 = MAX_uint16_T;
    }

    act2_valve((uint8_T)(mixr1_v2_dev_B.applied_V > 0.0), tmp_0);

    /* End of MATLAB Function: '<Root>/MATLAB Function' */
  }

  if (rtmIsMajorTimeStep(mixr1_v2_dev_M)) {
    if (rtmIsMajorTimeStep(mixr1_v2_dev_M)) {/* Sample time: [0.05s, 0.0s] */
      extmodeErrorCode_T errorCode = EXTMODE_SUCCESS;
      extmodeSimulationTime_T extmodeTime = (extmodeSimulationTime_T)
        ((mixr1_v2_dev_M->Timing.clockTick1 * 1) + 0);

      /* Trigger External Mode event */
      errorCode = extmodeEvent(1, extmodeTime);
      if (errorCode != EXTMODE_SUCCESS) {
        /* Code to handle External Mode event errors
           may be added here */
      }
    }
  }                                    /* end MajorTimeStep */

  if (rtmIsMajorTimeStep(mixr1_v2_dev_M)) {
    rt_ertODEUpdateContinuousStates(&mixr1_v2_dev_M->solverInfo);

    /* Update absolute time for base rate */
    /* The "clockTick0" counts the number of times the code of this task has
     * been executed. The absolute time is the multiplication of "clockTick0"
     * and "Timing.stepSize0". Size of "clockTick0" ensures timer will not
     * overflow during the application lifespan selected.
     */
    ++mixr1_v2_dev_M->Timing.clockTick0;
    mixr1_v2_dev_M->Timing.t[0] = rtsiGetSolverStopTime
      (&mixr1_v2_dev_M->solverInfo);

    {
      /* Update absolute timer for sample time: [0.05s, 0.0s] */
      /* The "clockTick1" counts the number of times the code of this task has
       * been executed. The resolution of this integer timer is 0.05, which is the step size
       * of the task. Size of "clockTick1" ensures timer will not overflow during the
       * application lifespan selected.
       */
      mixr1_v2_dev_M->Timing.clockTick1++;
    }
  }                                    /* end MajorTimeStep */
}

/* Derivatives for root system: '<Root>' */
void mixr1_v2_dev_derivatives(void)
{
  XDot_mixr1_v2_dev_T *_rtXdot;
  _rtXdot = ((XDot_mixr1_v2_dev_T *) mixr1_v2_dev_M->derivs);

  /* Derivatives for TransferFcn: '<Root>/level_display (smoothed, display only — not used for control).' */
  _rtXdot->level_displaysmootheddisplayonl =
    mixr1_v2_dev_P.level_displaysmootheddisplayonl *
    mixr1_v2_dev_X.level_displaysmootheddisplayonl;
  _rtXdot->level_displaysmootheddisplayonl += mixr1_v2_dev_B.level;
}

/* Model initialize function */
void mixr1_v2_dev_initialize(void)
{
  /* Registration code */

  /* initialize non-finites */
  rt_InitInfAndNaN(sizeof(real_T));

  /* initialize real-time model */
  (void) memset((void *)mixr1_v2_dev_M, 0,
                sizeof(RT_MODEL_mixr1_v2_dev_T));

  {
    /* Setup solver object */
    rtsiSetSimTimeStepPtr(&mixr1_v2_dev_M->solverInfo,
                          &mixr1_v2_dev_M->Timing.simTimeStep);
    rtsiSetTPtr(&mixr1_v2_dev_M->solverInfo, &rtmGetTPtr(mixr1_v2_dev_M));
    rtsiSetStepSizePtr(&mixr1_v2_dev_M->solverInfo,
                       &mixr1_v2_dev_M->Timing.stepSize0);
    rtsiSetdXPtr(&mixr1_v2_dev_M->solverInfo, &mixr1_v2_dev_M->derivs);
    rtsiSetContStatesPtr(&mixr1_v2_dev_M->solverInfo, (real_T **)
                         &mixr1_v2_dev_M->contStates);
    rtsiSetNumContStatesPtr(&mixr1_v2_dev_M->solverInfo,
      &mixr1_v2_dev_M->Sizes.numContStates);
    rtsiSetNumPeriodicContStatesPtr(&mixr1_v2_dev_M->solverInfo,
      &mixr1_v2_dev_M->Sizes.numPeriodicContStates);
    rtsiSetPeriodicContStateIndicesPtr(&mixr1_v2_dev_M->solverInfo,
      &mixr1_v2_dev_M->periodicContStateIndices);
    rtsiSetPeriodicContStateRangesPtr(&mixr1_v2_dev_M->solverInfo,
      &mixr1_v2_dev_M->periodicContStateRanges);
    rtsiSetContStateDisabledPtr(&mixr1_v2_dev_M->solverInfo, (boolean_T**)
      &mixr1_v2_dev_M->contStateDisabled);
    rtsiSetErrorStatusPtr(&mixr1_v2_dev_M->solverInfo, (&rtmGetErrorStatus
      (mixr1_v2_dev_M)));
    rtsiSetRTModelPtr(&mixr1_v2_dev_M->solverInfo, mixr1_v2_dev_M);
  }

  rtsiSetSimTimeStep(&mixr1_v2_dev_M->solverInfo, MAJOR_TIME_STEP);
  rtsiSetIsMinorTimeStepWithModeChange(&mixr1_v2_dev_M->solverInfo, false);
  rtsiSetIsContModeFrozen(&mixr1_v2_dev_M->solverInfo, false);
  mixr1_v2_dev_M->intgData.y = mixr1_v2_dev_M->odeY;
  mixr1_v2_dev_M->intgData.f[0] = mixr1_v2_dev_M->odeF[0];
  mixr1_v2_dev_M->intgData.f[1] = mixr1_v2_dev_M->odeF[1];
  mixr1_v2_dev_M->intgData.f[2] = mixr1_v2_dev_M->odeF[2];
  mixr1_v2_dev_M->contStates = ((X_mixr1_v2_dev_T *) &mixr1_v2_dev_X);
  mixr1_v2_dev_M->contStateDisabled = ((XDis_mixr1_v2_dev_T *)
    &mixr1_v2_dev_XDis);
  mixr1_v2_dev_M->Timing.tStart = (0.0);
  rtsiSetSolverData(&mixr1_v2_dev_M->solverInfo, (void *)
                    &mixr1_v2_dev_M->intgData);
  rtsiSetSolverName(&mixr1_v2_dev_M->solverInfo,"ode3");
  rtmSetTPtr(mixr1_v2_dev_M, &mixr1_v2_dev_M->Timing.tArray[0]);
  rtmSetTFinal(mixr1_v2_dev_M, -1);
  mixr1_v2_dev_M->Timing.stepSize0 = 0.05;

  /* External mode info */
  mixr1_v2_dev_M->Sizes.checksums[0] = (215515721U);
  mixr1_v2_dev_M->Sizes.checksums[1] = (598678343U);
  mixr1_v2_dev_M->Sizes.checksums[2] = (259596422U);
  mixr1_v2_dev_M->Sizes.checksums[3] = (3008393499U);

  {
    static const sysRanDType rtAlwaysEnabled = SUBSYS_RAN_BC_ENABLE;
    static RTWExtModeInfo rt_ExtModeInfo;
    static const sysRanDType *systemRan[7];
    mixr1_v2_dev_M->extModeInfo = (&rt_ExtModeInfo);
    rteiSetSubSystemActiveVectorAddresses(&rt_ExtModeInfo, systemRan);
    systemRan[0] = &rtAlwaysEnabled;
    systemRan[1] = &rtAlwaysEnabled;
    systemRan[2] = &rtAlwaysEnabled;
    systemRan[3] = &rtAlwaysEnabled;
    systemRan[4] = &rtAlwaysEnabled;
    systemRan[5] = &rtAlwaysEnabled;
    systemRan[6] = &rtAlwaysEnabled;
    rteiSetModelMappingInfoPtr(mixr1_v2_dev_M->extModeInfo,
      &mixr1_v2_dev_M->SpecialInfo.mappingInfo);
    rteiSetChecksumsPtr(mixr1_v2_dev_M->extModeInfo,
                        mixr1_v2_dev_M->Sizes.checksums);
    rteiSetTFinalTicks(mixr1_v2_dev_M->extModeInfo, -1);
  }

  /* block I/O */
  (void) memset(((void *) &mixr1_v2_dev_B), 0,
                sizeof(B_mixr1_v2_dev_T));

  /* states (continuous) */
  {
    (void) memset((void *)&mixr1_v2_dev_X, 0,
                  sizeof(X_mixr1_v2_dev_T));
  }

  /* disabled states */
  {
    (void) memset((void *)&mixr1_v2_dev_XDis, 0,
                  sizeof(XDis_mixr1_v2_dev_T));
  }

  /* states (dwork) */
  (void) memset((void *)&mixr1_v2_dev_DW, 0,
                sizeof(DW_mixr1_v2_dev_T));

  /* InitializeConditions for TransferFcn: '<Root>/level_display (smoothed, display only — not used for control).' */
  mixr1_v2_dev_X.level_displaysmootheddisplayonl = 0.0;

  /* SystemInitialize for MATLAB Function: '<S2>/tof_read' */
  /* '<S8>:1:11' k = uint32(0); */
  /* '<S8>:1:12' frame = uint32(0); */
  /* '<S8>:1:13' lastDist = uint16(0); */
  /* '<S8>:1:14' started = false; */
  mixr1_v2_dev_DW.started_d = false;

  /* SystemInitialize for MATLAB Function: '<S2>/level_calc' */
  /* '<S7>:1:12' buf = zeros(1,3); */
  mixr1_v2_dev_DW.buf[0] = 0.0;
  mixr1_v2_dev_DW.buf[1] = 0.0;
  mixr1_v2_dev_DW.buf[2] = 0.0;

  /* '<S7>:1:12' n = 0; */
  mixr1_v2_dev_DW.n = 0.0;

  /* '<S7>:1:12' age = 1e6; */
  mixr1_v2_dev_DW.age = 1.0E+6;

  /* '<S7>:1:12' have = false; */
  mixr1_v2_dev_DW.have = false;

  /* '<S7>:1:13' lvl = 0; */
  mixr1_v2_dev_DW.lvl = 0.0;

  /* SystemInitialize for MATLAB Function: '<S1>/MATLAB Function' */
  /* '<S7>:1:13' rawV = 0; */
  /* '<S7>:1:13' corrV = 0; */
  /* '<S6>:1:17' , */
  /* '<S6>:1:17' sw = false; */
  mixr1_v2_dev_DW.sw = false;

  /* '<S6>:1:17' prevMode = 0; */
  mixr1_v2_dev_DW.prevMode = 0.0;

  /* '<S6>:1:17' armed = coder.target('Sfun'); */
  mixr1_v2_dev_DW.armed = false;

  /* SystemInitialize for MATLAB Function: '<S4>/pump_guard' */
  /* '<S9>:1:11' atCeiling = false; */
  mixr1_v2_dev_DW.atCeiling = false;

  /* '<S9>:1:11' runSteps = 0; */
  mixr1_v2_dev_DW.runSteps_g = 0.0;

  /* '<S9>:1:11' offSteps = 0; */
  mixr1_v2_dev_DW.offSteps_m = 0.0;

  /* '<S9>:1:11' latched = false; */
  mixr1_v2_dev_DW.latched_e = false;

  /* SystemInitialize for MATLAB Function: '<S5>/valve_guard' */
  /* '<S10>:1:10' atFloor = false; */
  mixr1_v2_dev_DW.atFloor = false;

  /* '<S10>:1:10' runSteps = 0; */
  mixr1_v2_dev_DW.runSteps = 0.0;

  /* '<S10>:1:10' offSteps = 0; */
  mixr1_v2_dev_DW.offSteps = 0.0;

  /* '<S10>:1:10' latched = false; */
  mixr1_v2_dev_DW.latched = false;

  /* SystemInitialize for MATLAB Function: '<Root>/MATLAB Function' */
  /* '<S3>:1:10' , */
  /* '<S3>:1:10' started = false; */
  mixr1_v2_dev_DW.started = false;
}

/* Model terminate function */
void mixr1_v2_dev_terminate(void)
{
  /* user code (Terminate function Body) */
  act2_stop();
}

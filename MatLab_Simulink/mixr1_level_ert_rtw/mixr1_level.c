/*
 * mixr1_level.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "mixr1_level".
 *
 * Model version              : 1.15
 * Simulink Coder version : 26.1 (R2026a) 20-Nov-2025
 * C source code generated on : Thu Nov  5 19:15:53 2026
 *
 * Target selection: ert.tlc
 * Embedded hardware selection: ARM Compatible->ARM Cortex-A (64-bit)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "mixr1_level.h"
#include "tof_wrapper.h"
#include "ctl_wrapper.h"
#include "act_wrapper.h"
#include "rtwtypes.h"
#include "mixr1_level_private.h"
#include "rt_nonfinite.h"
#include <math.h>
#include <string.h>

/* Exported block parameters */
real_T fc_drainTo = 0.0;               /* Variable: fc_drainTo
                                        * Referenced by: '<Root>/Constant5'
                                        */
real_T fc_overshoot = 20.0;            /* Variable: fc_overshoot
                                        * Referenced by: '<Root>/Constant7'
                                        */
real_T fc_pumpV = 6.0;                 /* Variable: fc_pumpV
                                        * Referenced by: '<Root>/Constant4'
                                        */
real_T fc_settle = 5.0;                /* Variable: fc_settle
                                        * Referenced by: '<Root>/Constant9'
                                        */
real_T fc_target = 50.0;               /* Variable: fc_target
                                        * Referenced by: '<Root>/Constant1'
                                        */
real_T fc_tofGain = 1.00901;           /* Variable: fc_tofGain
                                        * Referenced by: '<S2>/Constant10'
                                        */
real_T fc_tofIntercept = 14.477;       /* Variable: fc_tofIntercept
                                        * Referenced by: '<S2>/Constant12'
                                        */
real_T fc_tol = 2.0;                   /* Variable: fc_tol
                                        * Referenced by: '<Root>/Constant8'
                                        */
real_T fc_valveV = 6.0;                /* Variable: fc_valveV
                                        * Referenced by: '<Root>/Constant6'
                                        */
uint8_T fc_cmd = 0U;                   /* Variable: fc_cmd
                                        * Referenced by: '<Root>/Constant'
                                        */

/* Block signals (default storage) */
B_mixr1_level_T mixr1_level_B;

/* Block states (default storage) */
DW_mixr1_level_T mixr1_level_DW;

/* Real-time model */
static RT_MODEL_mixr1_level_T mixr1_level_M_;
RT_MODEL_mixr1_level_T *const mixr1_level_M = &mixr1_level_M_;

/* Forward declaration for local functions */
static real_T mixr1_level_median(const real_T x_data[], const int32_T x_size[2]);
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

/* Function for MATLAB Function: '<Root>/fluid_ctrl' */
static real_T mixr1_level_median(const real_T x_data[], const int32_T x_size[2])
{
  real_T tmp;
  real_T y;
  real_T y_tmp;
  int32_T j2;
  switch (x_size[1]) {
   case 1:
    y = x_data[0];
    break;

   case 2:
    y_tmp = x_data[0];
    y = (x_data[1] - y_tmp) / 2.0 + y_tmp;
    break;

   default:
    y_tmp = x_data[0];
    tmp = x_data[1];
    if (y_tmp < tmp) {
      if (tmp < x_data[2]) {
        j2 = 1;
      } else if (y_tmp < x_data[2]) {
        j2 = 2;
      } else {
        j2 = 0;
      }
    } else if (y_tmp < x_data[2]) {
      j2 = 0;
    } else if (tmp < x_data[2]) {
      j2 = 2;
    } else {
      j2 = 1;
    }

    y = x_data[j2];
    break;
  }

  return y;
}

real_T rt_powd_snf(real_T u0, real_T u1)
{
  real_T tmp;
  real_T tmp_0;
  real_T y;
  if (rtIsNaN(u0) || rtIsNaN(u1)) {
    y = (rtNaN);
  } else {
    tmp = fabs(u0);
    tmp_0 = fabs(u1);
    if (rtIsInf(u1)) {
      if (tmp == 1.0) {
        y = 1.0;
      } else if (tmp > 1.0) {
        if (u1 > 0.0) {
          y = (rtInf);
        } else {
          y = 0.0;
        }
      } else if (u1 > 0.0) {
        y = 0.0;
      } else {
        y = (rtInf);
      }
    } else if (tmp_0 == 0.0) {
      y = 1.0;
    } else if (tmp_0 == 1.0) {
      if (u1 > 0.0) {
        y = u0;
      } else {
        y = 1.0 / u0;
      }
    } else if (u1 == 2.0) {
      y = u0 * u0;
    } else if ((u1 == 0.5) && (u0 >= 0.0)) {
      y = sqrt(u0);
    } else if ((u0 < 0.0) && (u1 > floor(u1))) {
      y = (rtNaN);
    } else {
      y = pow(u0, u1);
    }
  }

  return y;
}

/* Model step function */
void mixr1_level_step(void)
{
  real_T defs[17];
  real_T vals[17];
  real_T tmp_data[3];
  real_T ld;
  real_T ts;
  real_T u1;
  real_T x;
  int32_T tmp_size[2];
  int32_T i;
  int32_T limit;
  uint8_T c;
  boolean_T ok;

  /* MATLAB Function: '<S2>/tof_read' */
  /* MATLAB Function 'ToF_Calibrated/tof_read': '<S5>:1' */
  /* '<S5>:1:2' coder.extrinsic('which', 'fileparts'); */
  /* '<S5>:1:3' dist    = uint16(0); */
  /* '<S5>:1:4' status  = uint8(255); */
  /* '<S5>:1:5' newData = uint8(0); */
  /* '<S5>:1:8' if isempty(k) */
  /* '<S5>:1:13' if coder.target('Sfun') */
  /* '<S5>:1:18' else */
  /* '<S5>:1:19' srcDir = coder.const(fileparts(which('tof_wrapper.c'))); */
  /* '<S5>:1:20' coder.cinclude('tof_wrapper.h'); */
  /* '<S5>:1:21' coder.updateBuildInfo('addIncludePaths', srcDir); */
  /* '<S5>:1:22' coder.updateBuildInfo('addSourcePaths',  srcDir); */
  /* '<S5>:1:23' coder.updateBuildInfo('addSourceFiles', 'tof_wrapper.c'); */
  /* '<S5>:1:24' coder.updateBuildInfo('addSourceFiles', 'VL53L4CD_api.c'); */
  /* '<S5>:1:25' coder.updateBuildInfo('addSourceFiles', 'platform.c'); */
  /* '<S5>:1:27' if ~started */
  if (!mixr1_level_DW.started) {
    /* '<S5>:1:28' coder.ceval('tof_init', int16(-26), uint16(200)); */
    tof_init(-26, 200);

    /* '<S5>:1:29' started = true; */
    mixr1_level_DW.started = true;
  }

  /* '<S5>:1:31' coder.ceval('tof_step', coder.wref(dist), coder.wref(status), coder.wref(newData)); */
  tof_step(&mixr1_level_B.dist, &mixr1_level_B.status, &mixr1_level_B.newData);

  /* End of MATLAB Function: '<S2>/tof_read' */

  /* MATLAB Function: '<S2>/tof_read1' incorporates:
   *  Constant: '<S2>/Constant10'
   *  Constant: '<S2>/Constant12'
   */
  /* MATLAB Function 'ToF_Calibrated/tof_read1': '<S6>:1' */
  /* '<S6>:1:3' if dist == 0 */
  if (mixr1_level_B.dist == 0) {
    /* '<S6>:1:4' d = 0; */
    mixr1_level_B.d = 0.0;
  } else {
    /* '<S6>:1:5' else */
    /* '<S6>:1:6' d = (double(dist) - intercept) / gain; */
    mixr1_level_B.d = ((real_T)mixr1_level_B.dist - fc_tofIntercept) /
      fc_tofGain;
  }

  /* End of MATLAB Function: '<S2>/tof_read1' */

  /* MATLAB Function: '<Root>/fluid_ctrl' incorporates:
   *  Constant: '<Root>/Constant'
   *  Constant: '<Root>/Constant1'
   *  Constant: '<Root>/Constant2'
   *  Constant: '<Root>/Constant3'
   *  Constant: '<Root>/Constant4'
   *  Constant: '<Root>/Constant5'
   *  Constant: '<Root>/Constant6'
   *  Constant: '<Root>/Constant7'
   *  Constant: '<Root>/Constant8'
   *  Constant: '<Root>/Constant9'
   */
  /* MATLAB Function 'fluid_ctrl': '<S3>:1' */
  /* '<S3>:1:12' coder.extrinsic('which', 'fileparts'); */
  /* '<S3>:1:13' DT         = 0.05; */
  /* '<S3>:1:14' GAP_STEPS  = 2; */
  /* '<S3>:1:15' N_MED      = 3; */
  /* '<S3>:1:16' MAX_AGE    = 12; */
  /* '<S3>:1:17' EMPTY_MM   = 2.0; */
  /* '<S3>:1:18' MAX_BAD    = 10; */
  /* '<S3>:1:19' MAX_SILENT = 40; */
  /* '<S3>:1:20' MAX_RUN    = 4800; */
  /* '<S3>:1:21' BIG_MM     = 10; */
  /* '<S3>:1:22' BACKOFF    = 0.7; */
  /* '<S3>:1:23' SCALE_MIN  = 0.2; */
  /* '<S3>:1:24' V_MAX      = 24.0; */
  /* '<S3>:1:25' PWM_RANGE  = 1024; */
  /* '<S3>:1:29' if isempty(st) */
  /* '<S3>:1:37' defs = [double(cmd), target, pumpV, valveV, drainTo, overshoot, tol, settle, zero, thickness, ... */
  /* '<S3>:1:38'         1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0]; */
  defs[0] = fc_cmd;
  defs[1] = fc_target;
  defs[2] = fc_pumpV;
  defs[3] = fc_valveV;
  defs[4] = fc_drainTo;
  defs[5] = fc_overshoot;
  defs[6] = fc_tol;
  defs[7] = fc_settle;
  defs[8] = mixr1_level_P.Constant2_Value;
  defs[9] = mixr1_level_P.Constant3_Value;
  defs[10] = 1.0;
  defs[11] = 0.0;
  defs[12] = 1.0;
  defs[13] = 1.0;
  defs[14] = 1.0;
  defs[15] = 0.0;
  defs[16] = 0.0;

  /* '<S3>:1:39' vals = defs; */
  /* '<S3>:1:40' if ~coder.target('Sfun') */
  /* '<S3>:1:41' srcDir = coder.const(fileparts(which('ctl_wrapper.c'))); */
  /* '<S3>:1:42' coder.cinclude('ctl_wrapper.h'); */
  /* '<S3>:1:43' coder.updateBuildInfo('addIncludePaths', srcDir); */
  /* '<S3>:1:44' coder.updateBuildInfo('addSourcePaths',  srcDir); */
  /* '<S3>:1:45' coder.updateBuildInfo('addSourceFiles', 'ctl_wrapper.c'); */
  /* '<S3>:1:46' if ~ctlStarted */
  if (!mixr1_level_DW.ctlStarted) {
    /* '<S3>:1:47' coder.ceval('ctl_init'); */
    ctl_init();

    /* '<S3>:1:48' ctlStarted = true; */
    mixr1_level_DW.ctlStarted = true;
  }

  /* '<S3>:1:50' coder.ceval('ctl_poll', coder.rref(defs), coder.wref(vals)); */
  ctl_poll(&defs[0], &vals[0]);

  /* '<S3>:1:52' c   = uint8(min(max(round(vals(1)), 0), 255)); */
  ld = rt_roundd_snf(vals[0]);
  if (!(ld >= 0.0)) {
    ld = 0.0;
  }

  if (ld <= 255.0) {
    c = (uint8_T)ld;
  } else {
    c = MAX_uint8_T;
  }

  /* '<S3>:1:53' tgt = vals(2); */
  /* '<S3>:1:53' pV = vals(3); */
  /* '<S3>:1:53' vV = vals(4); */
  /* '<S3>:1:53' dTo = vals(5); */
  /* '<S3>:1:54' ovs = vals(6); */
  /* '<S3>:1:54' tl = vals(7); */
  /* '<S3>:1:54' stl = vals(8); */
  /* '<S3>:1:54' z0 = vals(9); */
  /* '<S3>:1:54' th = vals(10); */
  /* '<S3>:1:55' lg  = vals(11); */
  /* '<S3>:1:56' ld  = max(vals(12), 0); */
  if (vals[11] >= 0.0) {
    ld = vals[11];
  } else {
    ld = 0.0;
  }

  /* '<S3>:1:57' ts  = min(max(vals(13), 0), 1); */
  if (vals[12] >= 0.0) {
    ts = vals[12];
  } else {
    ts = 0.0;
  }

  if (!(ts <= 1.0)) {
    ts = 1.0;
  }

  /* '<S3>:1:58' rc  = max(vals(14), 0.2); */
  /* '<S3>:1:59' hd  = vals(15) >= 0.5; */
  /* '<S3>:1:60' lowRaw = vals(16); */
  /* '<S3>:1:61' sq  = vals(17); */
  /* '<S3>:1:62' settleSteps = round(stl / DT); */
  /* '<S3>:1:63' reactSteps  = round(rc / DT); */
  /* '<S3>:1:64' if lowRaw <= 0 */
  if (vals[15] <= 0.0) {
    /* '<S3>:1:65' lowEff = tgt - 10; */
    x = vals[1] - 10.0;
  } else {
    /* '<S3>:1:66' else */
    /* '<S3>:1:67' lowEff = lowRaw; */
    x = vals[15];
  }

  /* '<S3>:1:69' lowEff = min(lowEff, tgt - max(tl, 2)); */
  /* '<S3>:1:72' if newData == 1 */
  if (mixr1_level_B.newData == 1) {
    /* '<S3>:1:73' silent = 0; */
    mixr1_level_DW.silent = 0.0;

    /* '<S3>:1:74' if status == 0 && dist > 30 && dist <= 2000 */
    if ((mixr1_level_B.status == 0) && (mixr1_level_B.d > 30.0) &&
        (mixr1_level_B.d <= 2000.0)) {
      /* '<S3>:1:75' buf = [buf(2:3), double(dist)]; */
      mixr1_level_DW.buf[0] = mixr1_level_DW.buf[1];
      mixr1_level_DW.buf[1] = mixr1_level_DW.buf[2];
      mixr1_level_DW.buf[2] = mixr1_level_B.d;

      /* '<S3>:1:76' nvalid = min(nvalid + 1, 3); */
      if (mixr1_level_DW.nvalid + 1.0 <= 3.0) {
        mixr1_level_DW.nvalid++;
      } else {
        mixr1_level_DW.nvalid = 3.0;
      }

      /* '<S3>:1:77' bad = 0; */
      mixr1_level_DW.bad = 0.0;

      /* '<S3>:1:78' nuse = min(nvalid, N_MED); */
      /* '<S3>:1:79' lvl = max(0, lg * (z0 - median(buf(4-nuse:3)) - th)); */
      tmp_size[0] = 1;
      limit = 4 - (int32_T)(4.0 - mixr1_level_DW.nvalid);
      tmp_size[1] = 4 - (int32_T)(4.0 - mixr1_level_DW.nvalid);
      for (i = 0; i < limit; i++) {
        tmp_data[i] = mixr1_level_DW.buf[((int32_T)(4.0 - mixr1_level_DW.nvalid)
          + i) - 1];
      }

      u1 = ((vals[8] - mixr1_level_median(tmp_data, tmp_size)) - vals[9]) *
        vals[10];
      if ((u1 <= 0.0) || rtIsNaN(u1)) {
        mixr1_level_DW.lvl = 0.0;
      } else {
        mixr1_level_DW.lvl = u1;
      }

      /* '<S3>:1:80' haveLvl = true; */
      mixr1_level_DW.haveLvl = true;
    } else {
      /* '<S3>:1:81' else */
      /* '<S3>:1:82' bad = bad + 1; */
      mixr1_level_DW.bad++;
    }

    /* '<S3>:1:84' else */
    /* '<S3>:1:85' silent = min(silent + 1, 1e6); */
  } else if (mixr1_level_DW.silent + 1.0 <= 1.0E+6) {
    mixr1_level_DW.silent++;
  } else {
    mixr1_level_DW.silent = 1.0E+6;
  }

  /* '<S3>:1:89' newCmd = (c ~= prevCmd) || (sq ~= prevSeq); */
  /* '<S3>:1:90' if c == 0 */
  if (c == 0) {
    /* '<S3>:1:91' st = uint8(0); */
    mixr1_level_DW.st = 0U;

    /* '<S3>:1:92' why = uint8(0); */
    /* '<S3>:1:92' pending = uint8(0); */
    mixr1_level_DW.pending = 0U;

    /* '<S3>:1:92' gap = 0; */
    mixr1_level_DW.gap = 0.0;
  } else if (((c != mixr1_level_DW.prevCmd) || (vals[16] !=
               mixr1_level_DW.prevSeq)) && (c <= 7)) {
    /* '<S3>:1:93' elseif newCmd && c <= 7 */
    /* '<S3>:1:94' st = uint8(0); */
    mixr1_level_DW.st = 0U;

    /* '<S3>:1:95' why = uint8(0); */
    /* '<S3>:1:96' pending = c; */
    mixr1_level_DW.pending = c;

    /* '<S3>:1:96' gap = GAP_STEPS; */
    mixr1_level_DW.gap = 2.0;

    /* '<S3>:1:97' bad = 0; */
    mixr1_level_DW.bad = 0.0;

    /* '<S3>:1:97' runSteps = 0; */
    mixr1_level_DW.runSteps = 0.0;

    /* '<S3>:1:97' outSteps = 0; */
    mixr1_level_DW.outSteps = 0.0;

    /* '<S3>:1:97' fails = 0; */
    mixr1_level_DW.fails = 0.0;

    /* '<S3>:1:97' curScale = 1; */
    mixr1_level_DW.curScale = 1.0;
  } else if (mixr1_level_DW.pending != 0) {
    /* '<S3>:1:98' elseif pending ~= 0 */
    /* '<S3>:1:99' gap = gap - 1; */
    mixr1_level_DW.gap--;

    /* '<S3>:1:100' if gap <= 0 */
    if (mixr1_level_DW.gap <= 0.0) {
      /* '<S3>:1:101' if pending == 3 */
      switch (mixr1_level_DW.pending) {
       case 3U:
        /* '<S3>:1:102' st = uint8(5); */
        mixr1_level_DW.st = 5U;
        break;

       case 4U:
        /* '<S3>:1:103' elseif pending == 4 */
        /* '<S3>:1:104' st = uint8(6); */
        mixr1_level_DW.st = 6U;
        break;

       case 5U:
        /* '<S3>:1:105' elseif pending == 5 */
        /* '<S3>:1:106' st = uint8(11); */
        mixr1_level_DW.st = 11U;
        break;

       case 6U:
        /* '<S3>:1:107' elseif pending == 6 */
        /* '<S3>:1:108' st = uint8(12); */
        mixr1_level_DW.st = 12U;
        break;

       case 7U:
        /* '<S3>:1:109' elseif pending == 7 */
        /* '<S3>:1:110' st = uint8(13); */
        mixr1_level_DW.st = 13U;
        break;

       default:
        /* '<S3>:1:111' else */
        /* '<S3>:1:112' st = pending; */
        mixr1_level_DW.st = mixr1_level_DW.pending;
        break;
      }

      /* '<S3>:1:114' pending = uint8(0); */
      mixr1_level_DW.pending = 0U;
    }
  }

  /* '<S3>:1:117' prevCmd = c; */
  mixr1_level_DW.prevCmd = c;

  /* '<S3>:1:118' prevSeq = sq; */
  mixr1_level_DW.prevSeq = vals[16];

  /* '<S3>:1:121' if st ~= prevSt */
  if (mixr1_level_DW.st != mixr1_level_DW.prevSt) {
    /* '<S3>:1:122' runSteps = 0; */
    mixr1_level_DW.runSteps = 0.0;
  }

  /* '<S3>:1:124' prevSt = st; */
  mixr1_level_DW.prevSt = mixr1_level_DW.st;

  /* '<S3>:1:125' ok = haveLvl && silent <= MAX_AGE; */
  ok = (mixr1_level_DW.haveLvl && (mixr1_level_DW.silent <= 12.0));

  /* '<S3>:1:128' pumping  = (st == 1 || st == 5 || st == 8 || st == 14); */
  /* '<S3>:1:129' draining = (st == 2 || st == 7 || st == 13 || st == 14); */
  /* '<S3>:1:130' if pumping || draining */
  if ((mixr1_level_DW.st == 1) || (mixr1_level_DW.st == 5) || (mixr1_level_DW.st
       == 8) || (mixr1_level_DW.st == 14) || ((mixr1_level_DW.st == 2) ||
       (mixr1_level_DW.st == 7) || (mixr1_level_DW.st == 13) ||
       (mixr1_level_DW.st == 14))) {
    /* '<S3>:1:131' runSteps = runSteps + 1; */
    mixr1_level_DW.runSteps++;

    /* '<S3>:1:132' limit = MAX_RUN; */
    limit = 4800;

    /* '<S3>:1:133' if st == 13 */
    if (mixr1_level_DW.st == 13) {
      /* '<S3>:1:133' , */
      /* '<S3>:1:133' limit = 4 * MAX_RUN; */
      limit = 19200;
    }

    /* '<S3>:1:134' if bad >= MAX_BAD */
    if (mixr1_level_DW.bad >= 10.0) {
      /* '<S3>:1:135' st = uint8(9); */
      mixr1_level_DW.st = 9U;

      /* '<S3>:1:135' why = uint8(2); */
    } else if (mixr1_level_DW.silent >= 40.0) {
      /* '<S3>:1:136' elseif silent >= MAX_SILENT */
      /* '<S3>:1:137' st = uint8(9); */
      mixr1_level_DW.st = 9U;

      /* '<S3>:1:137' why = uint8(1); */
    } else if (mixr1_level_DW.runSteps >= limit) {
      /* '<S3>:1:138' elseif runSteps >= limit */
      /* '<S3>:1:139' st = uint8(9); */
      mixr1_level_DW.st = 9U;

      /* '<S3>:1:139' why = uint8(3); */
    } else if (mixr1_level_DW.haveLvl) {
      /* '<S3>:1:140' elseif haveLvl */
      /* '<S3>:1:141' if st == 1 */
      switch (mixr1_level_DW.st) {
       case 1U:
        /* '<S3>:1:142' if lvl >= tgt - ld */
        if (mixr1_level_DW.lvl >= vals[1] - ld) {
          /* '<S3>:1:142' , */
          /* '<S3>:1:142' st = uint8(3); */
          mixr1_level_DW.st = 3U;

          /* '<S3>:1:142' outSteps = 0; */
          mixr1_level_DW.outSteps = 0.0;
        }
        break;

       case 2U:
        /* '<S3>:1:143' elseif st == 2 */
        /* '<S3>:1:144' if lvl <= max(dTo, EMPTY_MM) */
        if (vals[4] >= 2.0) {
          u1 = vals[4];
        } else {
          u1 = 2.0;
        }

        if (mixr1_level_DW.lvl <= u1) {
          /* '<S3>:1:144' , */
          /* '<S3>:1:144' st = uint8(4); */
          mixr1_level_DW.st = 4U;
        }
        break;

       case 5U:
        /* '<S3>:1:145' elseif st == 5 */
        /* '<S3>:1:146' if lvl >= tgt + max(ovs, 0) - ld */
        if (vals[5] >= 0.0) {
          u1 = vals[5];
        } else {
          u1 = 0.0;
        }

        if (mixr1_level_DW.lvl >= (vals[1] + u1) - ld) {
          /* '<S3>:1:146' , */
          /* '<S3>:1:146' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 7U:
        /* '<S3>:1:147' elseif st == 7 */
        /* '<S3>:1:148' if lvl <= tgt + ld */
        if (mixr1_level_DW.lvl <= vals[1] + ld) {
          /* '<S3>:1:148' , */
          /* '<S3>:1:148' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 8U:
        /* '<S3>:1:149' elseif st == 8 */
        /* '<S3>:1:150' if lvl >= tgt - ld */
        if (mixr1_level_DW.lvl >= vals[1] - ld) {
          /* '<S3>:1:150' , */
          /* '<S3>:1:150' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 13U:
        /* '<S3>:1:151' elseif st == 13 */
        /* '<S3>:1:152' if lvl <= lowEff */
        if (vals[6] >= 2.0) {
          u1 = vals[6];
        } else {
          u1 = 2.0;
        }

        u1 = vals[1] - u1;
        if ((x <= u1) || rtIsNaN(u1)) {
          u1 = x;
        }

        if (mixr1_level_DW.lvl <= u1) {
          /* '<S3>:1:152' , */
          /* '<S3>:1:152' st = uint8(14); */
          mixr1_level_DW.st = 14U;
        }
        break;

       case 14U:
        /* '<S3>:1:153' elseif st == 14 */
        /* '<S3>:1:154' if lvl >= tgt - ld */
        if (mixr1_level_DW.lvl >= vals[1] - ld) {
          /* '<S3>:1:154' , */
          /* '<S3>:1:154' st = uint8(13); */
          mixr1_level_DW.st = 13U;
        }
        break;
      }
    }
  } else {
    switch (mixr1_level_DW.st) {
     case 6U:
      /* '<S3>:1:157' elseif st == 6 */
      /* '<S3>:1:158' runSteps = runSteps + 1; */
      mixr1_level_DW.runSteps++;

      /* '<S3>:1:159' if ok && runSteps >= settleSteps */
      if (ok && (mixr1_level_DW.runSteps >= rt_roundd_snf(vals[7] / 0.05))) {
        /* '<S3>:1:160' err = lvl - tgt; */
        ld = mixr1_level_DW.lvl - vals[1];

        /* '<S3>:1:161' if abs(err) <= tl */
        x = fabs(ld);
        if (x <= vals[6]) {
          /* '<S3>:1:162' st = uint8(3); */
          mixr1_level_DW.st = 3U;

          /* '<S3>:1:162' fails = 0; */
          mixr1_level_DW.fails = 0.0;

          /* '<S3>:1:162' outSteps = 0; */
          mixr1_level_DW.outSteps = 0.0;
        } else {
          /* '<S3>:1:163' else */
          /* '<S3>:1:164' fails = fails + 1; */
          mixr1_level_DW.fails++;

          /* '<S3>:1:165' if abs(err) > BIG_MM */
          if (x > 10.0) {
            /* '<S3>:1:166' curScale = 1; */
            mixr1_level_DW.curScale = 1.0;
          } else {
            /* '<S3>:1:167' else */
            /* '<S3>:1:168' curScale = max(SCALE_MIN, ts * BACKOFF^(fails - 1)); */
            u1 = rt_powd_snf(0.7, mixr1_level_DW.fails - 1.0) * ts;
            if ((u1 <= 0.2) || rtIsNaN(u1)) {
              mixr1_level_DW.curScale = 0.2;
            } else {
              mixr1_level_DW.curScale = u1;
            }
          }

          /* '<S3>:1:170' if err > 0 */
          if (ld > 0.0) {
            /* '<S3>:1:171' st = uint8(7); */
            mixr1_level_DW.st = 7U;
          } else {
            /* '<S3>:1:172' else */
            /* '<S3>:1:173' st = uint8(8); */
            mixr1_level_DW.st = 8U;
          }
        }
      }
      break;

     case 3U:
      if (vals[14] >= 0.5) {
        /* '<S3>:1:177' elseif st == 3 && hd */
        /* '<S3>:1:179' if ok && abs(lvl - tgt) > tl */
        if (ok) {
          if (fabs(mixr1_level_DW.lvl - vals[1]) > vals[6]) {
            /* '<S3>:1:180' outSteps = outSteps + 1; */
            mixr1_level_DW.outSteps++;

            /* '<S3>:1:181' else */
            /* '<S3>:1:182' outSteps = max(0, outSteps - 2); */
          } else if ((mixr1_level_DW.outSteps - 2.0 <= 0.0) || rtIsNaN
                     (mixr1_level_DW.outSteps - 2.0)) {
            mixr1_level_DW.outSteps = 0.0;
          } else {
            mixr1_level_DW.outSteps -= 2.0;
          }

          /* '<S3>:1:181' else */
          /* '<S3>:1:182' outSteps = max(0, outSteps - 2); */
        } else if ((mixr1_level_DW.outSteps - 2.0 <= 0.0) || rtIsNaN
                   (mixr1_level_DW.outSteps - 2.0)) {
          mixr1_level_DW.outSteps = 0.0;
        } else {
          mixr1_level_DW.outSteps -= 2.0;
        }

        /* '<S3>:1:184' if outSteps >= reactSteps */
        if (vals[13] >= 0.2) {
          u1 = vals[13];
        } else {
          u1 = 0.2;
        }

        if (mixr1_level_DW.outSteps >= rt_roundd_snf(u1 / 0.05)) {
          /* '<S3>:1:185' outSteps = 0; */
          mixr1_level_DW.outSteps = 0.0;

          /* '<S3>:1:185' fails = 1; */
          mixr1_level_DW.fails = 1.0;

          /* '<S3>:1:186' err = lvl - tgt; */
          ld = mixr1_level_DW.lvl - vals[1];

          /* '<S3>:1:187' if abs(err) > BIG_MM */
          if (fabs(ld) > 10.0) {
            /* '<S3>:1:188' curScale = 1; */
            mixr1_level_DW.curScale = 1.0;

            /* '<S3>:1:189' else */
            /* '<S3>:1:190' curScale = max(SCALE_MIN, ts); */
          } else if (ts <= 0.2) {
            mixr1_level_DW.curScale = 0.2;
          } else {
            mixr1_level_DW.curScale = ts;
          }

          /* '<S3>:1:192' if err > 0 */
          if (ld > 0.0) {
            /* '<S3>:1:193' st = uint8(7); */
            mixr1_level_DW.st = 7U;
          } else {
            /* '<S3>:1:194' else */
            /* '<S3>:1:195' st = uint8(8); */
            mixr1_level_DW.st = 8U;
          }
        }
      }
      break;
    }
  }

  /* '<S3>:1:201' if st == 11 || st == 12 */
  if ((mixr1_level_DW.st == 11) || (mixr1_level_DW.st == 12)) {
    /* '<S3>:1:202' runSteps = runSteps + 1; */
    mixr1_level_DW.runSteps++;

    /* '<S3>:1:203' if runSteps >= MAX_RUN */
    if (mixr1_level_DW.runSteps >= 4800.0) {
      /* '<S3>:1:204' st = uint8(9); */
      mixr1_level_DW.st = 9U;

      /* '<S3>:1:204' why = uint8(3); */
    } else if ((mixr1_level_DW.st == 12) && mixr1_level_DW.haveLvl) {
      if (vals[5] >= 0.0) {
        u1 = vals[5];
      } else {
        u1 = 0.0;
      }

      if (mixr1_level_DW.lvl >= vals[1] + u1) {
        /* '<S3>:1:205' elseif st == 12 && haveLvl && lvl >= tgt + max(ovs, 0) */
        /* '<S3>:1:206' st = uint8(4); */
        mixr1_level_DW.st = 4U;
      }
    }
  }

  /* '<S3>:1:211' ok      = haveLvl && silent <= MAX_AGE; */
  /* '<S3>:1:212' pumpOn  = uint8(((st == 1 || st == 5 || st == 8 || st == 14) && ok) || st == 12); */
  /* '<S3>:1:213' valveOn = uint8(((st == 2 || st == 7 || st == 13 || st == 14) && ok) || st == 11); */
  /* '<S3>:1:214' scale = 1.0; */
  ts = 1.0;

  /* '<S3>:1:215' if st == 7 || st == 8 */
  if ((mixr1_level_DW.st == 7) || (mixr1_level_DW.st == 8)) {
    /* '<S3>:1:215' , */
    /* '<S3>:1:215' scale = curScale; */
    ts = mixr1_level_DW.curScale;
  }

  /* '<S3>:1:216' pumpPwm  = uint16(min(PWM_RANGE, max(0, round(scale * pV / V_MAX * PWM_RANGE)))); */
  u1 = rt_roundd_snf(ts * vals[2] / 24.0 * 1024.0);
  if ((u1 <= 0.0) || rtIsNaN(u1)) {
    u1 = 0.0;
  }

  if (u1 >= 1024.0) {
    mixr1_level_B.pumpPwm = 1024U;
  } else {
    mixr1_level_B.pumpPwm = (uint16_T)u1;
  }

  /* '<S3>:1:217' valvePwm = uint16(min(PWM_RANGE, max(0, round(scale * vV / V_MAX * PWM_RANGE)))); */
  /* '<S3>:1:218' level    = lvl; */
  mixr1_level_B.level = mixr1_level_DW.lvl;

  /* '<S3>:1:219' state    = st; */
  mixr1_level_B.state = mixr1_level_DW.st;

  /* MATLAB Function: '<Root>/Actuators' */
  /* '<S3>:1:220' reason   = why; */
  /* MATLAB Function 'Actuators': '<S1>:1' */
  /* '<S1>:1:2' coder.extrinsic('which', 'fileparts'); */
  /* '<S1>:1:4' if isempty(started) */
  /* '<S1>:1:5' if ~coder.target('Sfun') */
  /* '<S1>:1:6' srcDir = coder.const(fileparts(which('act_wrapper.c'))); */
  /* '<S1>:1:7' coder.cinclude('act_wrapper.h'); */
  /* '<S1>:1:8' coder.updateBuildInfo('addIncludePaths', srcDir); */
  /* '<S1>:1:9' coder.updateBuildInfo('addSourcePaths',  srcDir); */
  /* '<S1>:1:10' coder.updateBuildInfo('addSourceFiles', 'act_wrapper.c'); */
  /* '<S1>:1:11' coder.updateBuildInfo('addLinkFlags', '-lwiringPi'); */
  /* '<S1>:1:12' if ~started */
  if (!mixr1_level_DW.started_l) {
    /* '<S1>:1:13' coder.ceval('act_init'); */
    act_init();

    /* '<S1>:1:14' started = true; */
    mixr1_level_DW.started_l = true;
  }

  /* MATLAB Function: '<Root>/fluid_ctrl' */
  /* '<S1>:1:16' coder.ceval('act_step', pumpOn, pumpPwm, valveOn, valvePwm); */
  u1 = rt_roundd_snf(ts * vals[3] / 24.0 * 1024.0);
  if ((u1 <= 0.0) || rtIsNaN(u1)) {
    u1 = 0.0;
  }

  if (u1 >= 1024.0) {
    i = 1024;
  } else {
    i = (int32_T)u1;
  }

  /* MATLAB Function: '<Root>/Actuators' incorporates:
   *  MATLAB Function: '<Root>/fluid_ctrl'
   */
  act_step((uint8_T)((((mixr1_level_DW.st == 1) || (mixr1_level_DW.st == 5) ||
                       (mixr1_level_DW.st == 8) || (mixr1_level_DW.st == 14)) &&
                      ok) || (mixr1_level_DW.st == 12)), mixr1_level_B.pumpPwm,
           (uint8_T)((((mixr1_level_DW.st == 2) || (mixr1_level_DW.st == 7) ||
                       (mixr1_level_DW.st == 13) || (mixr1_level_DW.st == 14)) &&
                      ok) || (mixr1_level_DW.st == 11)), (uint16_T)i);

  /* MATLAB Function: '<Root>/pack_log' incorporates:
   *  Constant: '<Root>/fc_mark'
   */
  /* MATLAB Function 'pack_log': '<S4>:1' */
  /* '<S4>:1:2' y = [double(dist), double(status), double(newData), level, double(state), mark]; */
  mixr1_level_B.y[0] = mixr1_level_B.d;
  mixr1_level_B.y[1] = mixr1_level_B.status;
  mixr1_level_B.y[2] = mixr1_level_B.newData;
  mixr1_level_B.y[3] = mixr1_level_B.level;
  mixr1_level_B.y[4] = mixr1_level_B.state;
  mixr1_level_B.y[5] = mixr1_level_P.fc_mark_Value;

  /* Update absolute time for base rate */
  /* The "clockTick0" counts the number of times the code of this task has
   * been executed. The resolution of this integer timer is 0.05, which is the step size
   * of the task. Size of "clockTick0" ensures timer will not overflow during the
   * application lifespan selected.
   */
  mixr1_level_M->Timing.clockTick0++;
}

/* Model initialize function */
void mixr1_level_initialize(void)
{
  /* Registration code */

  /* initialize non-finites */
  rt_InitInfAndNaN(sizeof(real_T));

  /* initialize real-time model */
  (void) memset((void *)mixr1_level_M, 0,
                sizeof(RT_MODEL_mixr1_level_T));
  rtmSetTFinal(mixr1_level_M, -1);

  /* External mode info */
  mixr1_level_M->Sizes.checksums[0] = (3773295361U);
  mixr1_level_M->Sizes.checksums[1] = (574563902U);
  mixr1_level_M->Sizes.checksums[2] = (1603679017U);
  mixr1_level_M->Sizes.checksums[3] = (547424545U);

  {
    static const sysRanDType rtAlwaysEnabled = SUBSYS_RAN_BC_ENABLE;
    static RTWExtModeInfo rt_ExtModeInfo;
    static const sysRanDType *systemRan[6];
    mixr1_level_M->extModeInfo = (&rt_ExtModeInfo);
    rteiSetSubSystemActiveVectorAddresses(&rt_ExtModeInfo, systemRan);
    systemRan[0] = &rtAlwaysEnabled;
    systemRan[1] = &rtAlwaysEnabled;
    systemRan[2] = &rtAlwaysEnabled;
    systemRan[3] = &rtAlwaysEnabled;
    systemRan[4] = &rtAlwaysEnabled;
    systemRan[5] = &rtAlwaysEnabled;
    rteiSetModelMappingInfoPtr(mixr1_level_M->extModeInfo,
      &mixr1_level_M->SpecialInfo.mappingInfo);
    rteiSetChecksumsPtr(mixr1_level_M->extModeInfo,
                        mixr1_level_M->Sizes.checksums);
    rteiSetTFinalTicks(mixr1_level_M->extModeInfo, -1);
  }

  /* block I/O */
  (void) memset(((void *) &mixr1_level_B), 0,
                sizeof(B_mixr1_level_T));

  /* states (dwork) */
  (void) memset((void *)&mixr1_level_DW, 0,
                sizeof(DW_mixr1_level_T));

  /* SystemInitialize for MATLAB Function: '<S2>/tof_read' */
  /* '<S5>:1:9' k = uint16(0); */
  /* '<S5>:1:10' started = false; */
  mixr1_level_DW.started = false;

  /* SystemInitialize for MATLAB Function: '<Root>/fluid_ctrl' */
  /* '<S3>:1:30' st = uint8(0); */
  mixr1_level_DW.st = 0U;

  /* '<S3>:1:30' prevSt = uint8(0); */
  mixr1_level_DW.prevSt = 0U;

  /* '<S3>:1:30' prevCmd = uint8(0); */
  mixr1_level_DW.prevCmd = 0U;

  /* '<S3>:1:30' prevSeq = 0; */
  mixr1_level_DW.prevSeq = 0.0;

  /* '<S3>:1:31' buf = zeros(1,3); */
  mixr1_level_DW.buf[0] = 0.0;
  mixr1_level_DW.buf[1] = 0.0;
  mixr1_level_DW.buf[2] = 0.0;

  /* '<S3>:1:31' nvalid = 0; */
  mixr1_level_DW.nvalid = 0.0;

  /* '<S3>:1:31' bad = 0; */
  mixr1_level_DW.bad = 0.0;

  /* '<S3>:1:31' silent = 0; */
  mixr1_level_DW.silent = 0.0;

  /* '<S3>:1:31' runSteps = 0; */
  mixr1_level_DW.runSteps = 0.0;

  /* '<S3>:1:31' outSteps = 0; */
  mixr1_level_DW.outSteps = 0.0;

  /* '<S3>:1:32' fails = 0; */
  mixr1_level_DW.fails = 0.0;

  /* '<S3>:1:32' curScale = 1; */
  mixr1_level_DW.curScale = 1.0;

  /* '<S3>:1:32' lvl = 0; */
  mixr1_level_DW.lvl = 0.0;

  /* '<S3>:1:32' haveLvl = false; */
  mixr1_level_DW.haveLvl = false;

  /* '<S3>:1:33' why = uint8(0); */
  /* '<S3>:1:33' pending = uint8(0); */
  mixr1_level_DW.pending = 0U;

  /* '<S3>:1:33' gap = 0; */
  mixr1_level_DW.gap = 0.0;

  /* '<S3>:1:33' ctlStarted = false; */
  mixr1_level_DW.ctlStarted = false;

  /* SystemInitialize for MATLAB Function: '<Root>/Actuators' */
  /* '<S1>:1:4' , */
  /* '<S1>:1:4' started = false; */
  mixr1_level_DW.started_l = false;
}

/* Model terminate function */
void mixr1_level_terminate(void)
{
  /* (no terminate code required) */
}

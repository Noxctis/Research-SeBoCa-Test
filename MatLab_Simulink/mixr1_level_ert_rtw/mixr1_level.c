/*
 * mixr1_level.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "mixr1_level".
 *
 * Model version              : 1.13
 * Simulink Coder version : 26.1 (R2026a) 20-Nov-2025
 * C source code generated on : Wed Nov  4 23:47:32 2026
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
#include "mixr1_level_private.h"
#include "rt_nonfinite.h"
#include <math.h>
#include "rtwtypes.h"
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
void mixr1_level_step(void)
{
  real_T defs[14];
  real_T vals[14];
  real_T ld;
  real_T nuse;
  real_T tmp;
  int32_T j2;
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
  /* '<S3>:1:8' coder.extrinsic('which', 'fileparts'); */
  /* '<S3>:1:9' DT         = 0.05; */
  /* '<S3>:1:10' N_MED      = 3; */
  /* '<S3>:1:11' MAX_AGE    = 12; */
  /* '<S3>:1:12' EMPTY_MM   = 2.0; */
  /* '<S3>:1:13' MAX_BAD    = 10; */
  /* '<S3>:1:14' MAX_SILENT = 40; */
  /* '<S3>:1:15' MAX_RUN    = 4800; */
  /* '<S3>:1:16' MAX_TRIM   = 5; */
  /* '<S3>:1:17' V_MAX      = 24.0; */
  /* '<S3>:1:18' PWM_RANGE  = 1024; */
  /* '<S3>:1:21' if isempty(st) */
  /* '<S3>:1:28' defs = [double(cmd), target, pumpV, valveV, drainTo, overshoot, tol, settle, zero, thickness, ... */
  /* '<S3>:1:29'         1.0, 0.0, 1.0, 0.0]; */
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
  defs[13] = 0.0;

  /* '<S3>:1:30' vals = defs; */
  /* '<S3>:1:31' if ~coder.target('Sfun') */
  /* '<S3>:1:32' srcDir = coder.const(fileparts(which('ctl_wrapper.c'))); */
  /* '<S3>:1:33' coder.cinclude('ctl_wrapper.h'); */
  /* '<S3>:1:34' coder.updateBuildInfo('addIncludePaths', srcDir); */
  /* '<S3>:1:35' coder.updateBuildInfo('addSourcePaths',  srcDir); */
  /* '<S3>:1:36' coder.updateBuildInfo('addSourceFiles', 'ctl_wrapper.c'); */
  /* '<S3>:1:37' if ~ctlStarted */
  if (!mixr1_level_DW.ctlStarted) {
    /* '<S3>:1:38' coder.ceval('ctl_init'); */
    ctl_init();

    /* '<S3>:1:39' ctlStarted = true; */
    mixr1_level_DW.ctlStarted = true;
  }

  /* '<S3>:1:41' coder.ceval('ctl_poll', coder.rref(defs), coder.wref(vals)); */
  ctl_poll(&defs[0], &vals[0]);

  /* '<S3>:1:43' c   = uint8(min(max(round(vals(1)), 0), 255)); */
  ld = rt_roundd_snf(vals[0]);
  if (!(ld >= 0.0)) {
    ld = 0.0;
  }

  if (ld <= 255.0) {
    c = (uint8_T)ld;
  } else {
    c = MAX_uint8_T;
  }

  /* '<S3>:1:44' tgt = vals(2); */
  /* '<S3>:1:44' pV = vals(3); */
  /* '<S3>:1:44' vV = vals(4); */
  /* '<S3>:1:44' dTo = vals(5); */
  /* '<S3>:1:45' ovs = vals(6); */
  /* '<S3>:1:45' tl = vals(7); */
  /* '<S3>:1:45' stl = vals(8); */
  /* '<S3>:1:45' z0 = vals(9); */
  /* '<S3>:1:45' th = vals(10); */
  /* '<S3>:1:46' lg  = vals(11); */
  /* '<S3>:1:47' ld  = max(vals(12), 0); */
  if (vals[11] >= 0.0) {
    ld = vals[11];
  } else {
    ld = 0.0;
  }

  /* '<S3>:1:48' ts  = min(max(vals(13), 0), 1); */
  /* '<S3>:1:49' sq  = vals(14); */
  /* '<S3>:1:52' if newData == 1 */
  if (mixr1_level_B.newData == 1) {
    /* '<S3>:1:53' silent = 0; */
    mixr1_level_DW.silent = 0.0;

    /* '<S3>:1:54' if status == 0 && dist > 30 && dist <= 2000 */
    if ((mixr1_level_B.status == 0) && (mixr1_level_B.d > 30.0) &&
        (mixr1_level_B.d <= 2000.0)) {
      /* '<S3>:1:55' buf = [buf(2:3), double(dist)]; */
      mixr1_level_DW.buf[0] = mixr1_level_DW.buf[1];
      mixr1_level_DW.buf[1] = mixr1_level_DW.buf[2];
      mixr1_level_DW.buf[2] = mixr1_level_B.d;

      /* '<S3>:1:56' nvalid = min(nvalid + 1, 3); */
      if (mixr1_level_DW.nvalid + 1.0 <= 3.0) {
        mixr1_level_DW.nvalid++;
      } else {
        mixr1_level_DW.nvalid = 3.0;
      }

      /* '<S3>:1:57' bad = 0; */
      mixr1_level_DW.bad = 0.0;

      /* '<S3>:1:58' nuse = min(nvalid, N_MED); */
      /* '<S3>:1:59' lvl = max(0, lg * (z0 - median(buf(4-nuse:3)) - th)); */
      switch (4 - (int32_T)(4.0 - mixr1_level_DW.nvalid)) {
       case 1:
        nuse = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        break;

       case 2:
        nuse = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        nuse += (mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid)] -
                 nuse) / 2.0;
        break;

       default:
        nuse = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        tmp = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid)];
        if (nuse < tmp) {
          if (tmp < mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) +
              1]) {
            j2 = 1;
          } else if (nuse < mixr1_level_DW.buf[(int32_T)(4.0 -
                      mixr1_level_DW.nvalid) + 1]) {
            j2 = 2;
          } else {
            j2 = 0;
          }
        } else if (nuse < mixr1_level_DW.buf[(int32_T)(4.0 -
                    mixr1_level_DW.nvalid) + 1]) {
          j2 = 0;
        } else if (tmp < mixr1_level_DW.buf[(int32_T)(4.0 -
                    mixr1_level_DW.nvalid) + 1]) {
          j2 = 2;
        } else {
          j2 = 1;
        }

        nuse = mixr1_level_DW.buf[((int32_T)(4.0 - mixr1_level_DW.nvalid) + j2)
          - 1];
        break;
      }

      nuse = ((vals[8] - nuse) - vals[9]) * vals[10];
      if ((nuse <= 0.0) || rtIsNaN(nuse)) {
        mixr1_level_DW.lvl = 0.0;
      } else {
        mixr1_level_DW.lvl = nuse;
      }

      /* '<S3>:1:60' haveLvl = true; */
      mixr1_level_DW.haveLvl = true;
    } else {
      /* '<S3>:1:61' else */
      /* '<S3>:1:62' bad = bad + 1; */
      mixr1_level_DW.bad++;
    }

    /* '<S3>:1:64' else */
    /* '<S3>:1:65' silent = min(silent + 1, 1e6); */
  } else if (mixr1_level_DW.silent + 1.0 <= 1.0E+6) {
    mixr1_level_DW.silent++;
  } else {
    mixr1_level_DW.silent = 1.0E+6;
  }

  /* '<S3>:1:69' newCmd = (c ~= prevCmd) || (sq ~= prevSeq); */
  /* '<S3>:1:70' if c == 0 */
  if (c == 0) {
    /* '<S3>:1:71' st = uint8(0); */
    mixr1_level_DW.st = 0U;

    /* '<S3>:1:72' holdMode = false; */
    mixr1_level_DW.holdMode = false;
  } else if (((c != mixr1_level_DW.prevCmd) || (vals[13] !=
               mixr1_level_DW.prevSeq)) && (mixr1_level_DW.st != 9) && (c <= 6))
  {
    /* '<S3>:1:73' elseif newCmd && st ~= 9 && c <= 6 */
    /* '<S3>:1:74' holdMode = (c == 4); */
    mixr1_level_DW.holdMode = (c == 4);

    /* '<S3>:1:75' if c == 3 */
    switch (c) {
     case 3U:
      /* '<S3>:1:76' st = uint8(5); */
      mixr1_level_DW.st = 5U;
      break;

     case 4U:
      /* '<S3>:1:77' elseif c == 4 */
      /* '<S3>:1:78' st = uint8(10); */
      mixr1_level_DW.st = 10U;
      break;

     case 5U:
      /* '<S3>:1:79' elseif c == 5 */
      /* '<S3>:1:80' st = uint8(11); */
      mixr1_level_DW.st = 11U;
      break;

     case 6U:
      /* '<S3>:1:81' elseif c == 6 */
      /* '<S3>:1:82' st = uint8(12); */
      mixr1_level_DW.st = 12U;
      break;

     default:
      /* '<S3>:1:83' else */
      /* '<S3>:1:84' st = c; */
      mixr1_level_DW.st = c;
      break;
    }

    /* '<S3>:1:86' bad = 0; */
    mixr1_level_DW.bad = 0.0;

    /* '<S3>:1:86' runSteps = 0; */
    mixr1_level_DW.runSteps = 0.0;

    /* '<S3>:1:86' outSteps = 0; */
    mixr1_level_DW.outSteps = 0.0;

    /* '<S3>:1:86' trims = 0; */
    mixr1_level_DW.trims = 0.0;
  }

  /* '<S3>:1:88' prevCmd = c; */
  mixr1_level_DW.prevCmd = c;

  /* '<S3>:1:89' prevSeq = sq; */
  mixr1_level_DW.prevSeq = vals[13];

  /* '<S3>:1:92' if st ~= prevSt */
  if (mixr1_level_DW.st != mixr1_level_DW.prevSt) {
    /* '<S3>:1:93' runSteps = 0; */
    mixr1_level_DW.runSteps = 0.0;
  }

  /* '<S3>:1:95' prevSt = st; */
  mixr1_level_DW.prevSt = mixr1_level_DW.st;

  /* '<S3>:1:98' active = (st == 1 || st == 2 || st == 5 || st == 6 || st == 7 || st == 8 || st == 10); */
  /* '<S3>:1:99' if active */
  if ((mixr1_level_DW.st == 1) || (mixr1_level_DW.st == 2) || (mixr1_level_DW.st
       == 5) || (mixr1_level_DW.st == 6) || (mixr1_level_DW.st == 7) ||
      (mixr1_level_DW.st == 8) || (mixr1_level_DW.st == 10)) {
    /* '<S3>:1:100' runSteps = runSteps + 1; */
    mixr1_level_DW.runSteps++;

    /* '<S3>:1:101' if bad >= MAX_BAD || silent >= MAX_SILENT || ... */
    /* '<S3>:1:102'             (st ~= 6 && st ~= 10 && runSteps >= MAX_RUN) */
    if ((mixr1_level_DW.bad >= 10.0) || (mixr1_level_DW.silent >= 40.0) ||
        ((mixr1_level_DW.st != 6) && (mixr1_level_DW.st != 10) &&
         (mixr1_level_DW.runSteps >= 4800.0))) {
      /* '<S3>:1:103' st = uint8(9); */
      mixr1_level_DW.st = 9U;
    } else if (mixr1_level_DW.haveLvl) {
      /* '<S3>:1:104' elseif haveLvl */
      /* '<S3>:1:105' if st == 1 */
      switch (mixr1_level_DW.st) {
       case 1U:
        /* '<S3>:1:106' if lvl >= tgt - ld */
        if (mixr1_level_DW.lvl >= vals[1] - ld) {
          /* '<S3>:1:106' , */
          /* '<S3>:1:106' st = uint8(3); */
          mixr1_level_DW.st = 3U;
        }
        break;

       case 2U:
        /* '<S3>:1:107' elseif st == 2 */
        /* '<S3>:1:108' if lvl <= max(dTo, EMPTY_MM) */
        if (vals[4] >= 2.0) {
          nuse = vals[4];
        } else {
          nuse = 2.0;
        }

        if (mixr1_level_DW.lvl <= nuse) {
          /* '<S3>:1:108' , */
          /* '<S3>:1:108' st = uint8(4); */
          mixr1_level_DW.st = 4U;
        }
        break;

       case 5U:
        /* '<S3>:1:109' elseif st == 5 */
        /* '<S3>:1:110' if lvl >= tgt + max(ovs, 0) - ld */
        if (vals[5] >= 0.0) {
          nuse = vals[5];
        } else {
          nuse = 0.0;
        }

        if (mixr1_level_DW.lvl >= (vals[1] + nuse) - ld) {
          /* '<S3>:1:110' , */
          /* '<S3>:1:110' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 6U:
        /* '<S3>:1:111' elseif st == 6 */
        /* '<S3>:1:112' if runSteps >= round(stl / DT) */
        if (mixr1_level_DW.runSteps >= rt_roundd_snf(vals[7] / 0.05)) {
          /* '<S3>:1:113' err = lvl - tgt; */
          ld = mixr1_level_DW.lvl - vals[1];

          /* '<S3>:1:114' if abs(err) <= tl */
          if (fabs(ld) <= vals[6]) {
            /* '<S3>:1:115' if holdMode */
            if (mixr1_level_DW.holdMode) {
              /* '<S3>:1:116' st = uint8(10); */
              mixr1_level_DW.st = 10U;

              /* '<S3>:1:116' outSteps = 0; */
              mixr1_level_DW.outSteps = 0.0;

              /* '<S3>:1:116' trims = 0; */
              mixr1_level_DW.trims = 0.0;
            } else {
              /* '<S3>:1:117' else */
              /* '<S3>:1:118' st = uint8(3); */
              mixr1_level_DW.st = 3U;
            }
          } else if (mixr1_level_DW.trims >= 5.0) {
            /* '<S3>:1:120' elseif trims >= MAX_TRIM */
            /* '<S3>:1:121' st = uint8(9); */
            mixr1_level_DW.st = 9U;
          } else if (ld > 0.0) {
            /* '<S3>:1:122' elseif err > 0 */
            /* '<S3>:1:123' st = uint8(7); */
            mixr1_level_DW.st = 7U;

            /* '<S3>:1:123' trims = trims + 1; */
            mixr1_level_DW.trims++;
          } else {
            /* '<S3>:1:124' else */
            /* '<S3>:1:125' st = uint8(8); */
            mixr1_level_DW.st = 8U;

            /* '<S3>:1:125' trims = trims + 1; */
            mixr1_level_DW.trims++;
          }
        }
        break;

       case 7U:
        /* '<S3>:1:128' elseif st == 7 */
        /* '<S3>:1:129' if lvl <= tgt + ld */
        if (mixr1_level_DW.lvl <= vals[1] + ld) {
          /* '<S3>:1:129' , */
          /* '<S3>:1:129' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 8U:
        /* '<S3>:1:130' elseif st == 8 */
        /* '<S3>:1:131' if lvl >= tgt - ld */
        if (mixr1_level_DW.lvl >= vals[1] - ld) {
          /* '<S3>:1:131' , */
          /* '<S3>:1:131' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 10U:
        /* '<S3>:1:132' elseif st == 10 */
        /* '<S3>:1:133' if abs(lvl - tgt) > tl */
        if (fabs(mixr1_level_DW.lvl - vals[1]) > vals[6]) {
          /* '<S3>:1:134' outSteps = outSteps + 1; */
          mixr1_level_DW.outSteps++;
        } else {
          /* '<S3>:1:135' else */
          /* '<S3>:1:136' outSteps = 0; */
          mixr1_level_DW.outSteps = 0.0;
        }

        /* '<S3>:1:138' if outSteps >= round(stl / DT) */
        if (mixr1_level_DW.outSteps >= rt_roundd_snf(vals[7] / 0.05)) {
          /* '<S3>:1:139' outSteps = 0; */
          mixr1_level_DW.outSteps = 0.0;

          /* '<S3>:1:140' trims = trims + 1; */
          mixr1_level_DW.trims++;

          /* '<S3>:1:141' if lvl > tgt */
          if (mixr1_level_DW.lvl > vals[1]) {
            /* '<S3>:1:142' st = uint8(7); */
            mixr1_level_DW.st = 7U;
          } else {
            /* '<S3>:1:143' else */
            /* '<S3>:1:144' st = uint8(8); */
            mixr1_level_DW.st = 8U;
          }
        }
        break;
      }
    }
  }

  /* '<S3>:1:152' if st == 11 || st == 12 */
  if ((mixr1_level_DW.st == 11) || (mixr1_level_DW.st == 12)) {
    /* '<S3>:1:153' runSteps = runSteps + 1; */
    mixr1_level_DW.runSteps++;

    /* '<S3>:1:154' if runSteps >= MAX_RUN */
    if (mixr1_level_DW.runSteps >= 4800.0) {
      /* '<S3>:1:155' st = uint8(9); */
      mixr1_level_DW.st = 9U;
    } else if ((mixr1_level_DW.st == 12) && mixr1_level_DW.haveLvl) {
      if (vals[5] >= 0.0) {
        nuse = vals[5];
      } else {
        nuse = 0.0;
      }

      if (mixr1_level_DW.lvl >= vals[1] + nuse) {
        /* '<S3>:1:156' elseif st == 12 && haveLvl && lvl >= tgt + max(ovs, 0) */
        /* '<S3>:1:157' st = uint8(4); */
        mixr1_level_DW.st = 4U;
      }
    }
  }

  /* '<S3>:1:162' ok      = haveLvl && silent <= MAX_AGE; */
  ok = (mixr1_level_DW.haveLvl && (mixr1_level_DW.silent <= 12.0));

  /* '<S3>:1:163' pumpOn  = uint8(((st == 1 || st == 5 || st == 8) && ok) || st == 12); */
  /* '<S3>:1:164' valveOn = uint8(((st == 2 || st == 7) && ok) || st == 11); */
  /* '<S3>:1:165' scale = 1.0; */
  ld = 1.0;

  /* '<S3>:1:166' if st == 7 || st == 8 */
  if ((mixr1_level_DW.st == 7) || (mixr1_level_DW.st == 8)) {
    /* '<S3>:1:166' , */
    /* '<S3>:1:166' scale = ts; */
    if (vals[12] >= 0.0) {
      nuse = vals[12];
    } else {
      nuse = 0.0;
    }

    if (nuse <= 1.0) {
      ld = nuse;
    }
  }

  /* '<S3>:1:167' pumpPwm  = uint16(min(PWM_RANGE, max(0, round(scale * pV / V_MAX * PWM_RANGE)))); */
  nuse = rt_roundd_snf(ld * vals[2] / 24.0 * 1024.0);
  if ((nuse <= 0.0) || rtIsNaN(nuse)) {
    nuse = 0.0;
  }

  if (nuse >= 1024.0) {
    mixr1_level_B.pumpPwm = 1024U;
  } else {
    mixr1_level_B.pumpPwm = (uint16_T)nuse;
  }

  /* '<S3>:1:168' valvePwm = uint16(min(PWM_RANGE, max(0, round(scale * vV / V_MAX * PWM_RANGE)))); */
  /* '<S3>:1:169' level    = lvl; */
  mixr1_level_B.level = mixr1_level_DW.lvl;

  /* '<S3>:1:170' state    = st; */
  mixr1_level_B.state = mixr1_level_DW.st;

  /* MATLAB Function: '<Root>/Actuators' */
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
  nuse = rt_roundd_snf(ld * vals[3] / 24.0 * 1024.0);
  if ((nuse <= 0.0) || rtIsNaN(nuse)) {
    nuse = 0.0;
  }

  if (nuse >= 1024.0) {
    j2 = 1024;
  } else {
    j2 = (int32_T)nuse;
  }

  /* MATLAB Function: '<Root>/Actuators' incorporates:
   *  MATLAB Function: '<Root>/fluid_ctrl'
   */
  act_step((uint8_T)((((mixr1_level_DW.st == 1) || (mixr1_level_DW.st == 5) ||
                       (mixr1_level_DW.st == 8)) && ok) || (mixr1_level_DW.st ==
             12)), mixr1_level_B.pumpPwm, (uint8_T)((((mixr1_level_DW.st == 2) ||
              (mixr1_level_DW.st == 7)) && ok) || (mixr1_level_DW.st == 11)),
           (uint16_T)j2);

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
  mixr1_level_M->Sizes.checksums[0] = (2880802854U);
  mixr1_level_M->Sizes.checksums[1] = (2712775699U);
  mixr1_level_M->Sizes.checksums[2] = (555371141U);
  mixr1_level_M->Sizes.checksums[3] = (2330121893U);

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
  /* '<S3>:1:22' st = uint8(0); */
  mixr1_level_DW.st = 0U;

  /* '<S3>:1:22' prevSt = uint8(0); */
  mixr1_level_DW.prevSt = 0U;

  /* '<S3>:1:22' prevCmd = uint8(0); */
  mixr1_level_DW.prevCmd = 0U;

  /* '<S3>:1:22' prevSeq = 0; */
  mixr1_level_DW.prevSeq = 0.0;

  /* '<S3>:1:23' buf = zeros(1,3); */
  mixr1_level_DW.buf[0] = 0.0;
  mixr1_level_DW.buf[1] = 0.0;
  mixr1_level_DW.buf[2] = 0.0;

  /* '<S3>:1:23' nvalid = 0; */
  mixr1_level_DW.nvalid = 0.0;

  /* '<S3>:1:23' bad = 0; */
  mixr1_level_DW.bad = 0.0;

  /* '<S3>:1:23' silent = 0; */
  mixr1_level_DW.silent = 0.0;

  /* '<S3>:1:23' runSteps = 0; */
  mixr1_level_DW.runSteps = 0.0;

  /* '<S3>:1:23' outSteps = 0; */
  mixr1_level_DW.outSteps = 0.0;

  /* '<S3>:1:23' trims = 0; */
  mixr1_level_DW.trims = 0.0;

  /* '<S3>:1:24' lvl = 0; */
  mixr1_level_DW.lvl = 0.0;

  /* '<S3>:1:24' haveLvl = false; */
  mixr1_level_DW.haveLvl = false;

  /* '<S3>:1:24' holdMode = false; */
  mixr1_level_DW.holdMode = false;

  /* '<S3>:1:24' ctlStarted = false; */
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

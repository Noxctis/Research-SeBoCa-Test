/*
 * mixr1_level.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "mixr1_level".
 *
 * Model version              : 1.12
 * Simulink Coder version : 26.1 (R2026a) 20-Nov-2025
 * C source code generated on : Wed Nov  4 17:22:31 2026
 *
 * Target selection: ert.tlc
 * Embedded hardware selection: ARM Compatible->ARM Cortex-A (64-bit)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "mixr1_level.h"
#include "tof_wrapper.h"
#include "act_wrapper.h"
#include "rt_nonfinite.h"
#include "mixr1_level_private.h"
#include <math.h>
#include "rtwtypes.h"
#include <string.h>

/* Exported block parameters */
real_T fc_drainTo = 0.0;               /* Variable: fc_drainTo
                                        * Referenced by: '<Root>/Constant5'
                                        */
real_T fc_overshoot = 10.0;            /* Variable: fc_overshoot
                                        * Referenced by: '<Root>/Constant7'
                                        */
real_T fc_pumpV = 6.0;                 /* Variable: fc_pumpV
                                        * Referenced by: '<Root>/Constant4'
                                        */
real_T fc_settle = 5.0;                /* Variable: fc_settle
                                        * Referenced by: '<Root>/Constant9'
                                        */
real_T fc_target = 100.0;              /* Variable: fc_target
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
uint8_T fc_cmd = 2U;                   /* Variable: fc_cmd
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
  real_T d;
  real_T err;
  real_T tmp;
  int32_T j2;

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
    d = 0.0;
  } else {
    /* '<S6>:1:5' else */
    /* '<S6>:1:6' d = (double(dist) - intercept) / gain; */
    d = ((real_T)mixr1_level_B.dist - fc_tofIntercept) / fc_tofGain;
  }

  /* End of MATLAB Function: '<S2>/tof_read1' */

  /* MATLAB Function: '<Root>/fluid_ctrl' incorporates:
   *  Constant: '<Root>/Constant'
   *  Constant: '<Root>/Constant1'
   *  Constant: '<Root>/Constant2'
   *  Constant: '<Root>/Constant3'
   *  Constant: '<Root>/Constant4'
   *  Constant: '<Root>/Constant5'
   *  Constant: '<Root>/Constant7'
   *  Constant: '<Root>/Constant8'
   *  Constant: '<Root>/Constant9'
   */
  /* MATLAB Function 'fluid_ctrl': '<S3>:1' */
  /* '<S3>:1:7' DT         = 0.05; */
  /* '<S3>:1:8' EMPTY_MM   = 2.0; */
  /* '<S3>:1:9' MAX_BAD    = 10; */
  /* '<S3>:1:10' MAX_SILENT = 40; */
  /* '<S3>:1:11' MAX_RUN    = 4800; */
  /* '<S3>:1:12' MAX_TRIM   = 5; */
  /* '<S3>:1:13' V_MAX      = 12.0; */
  /* '<S3>:1:14' PWM_RANGE  = 1024; */
  /* '<S3>:1:17' if isempty(st) */
  /* '<S3>:1:24' if newData == 1 */
  if (mixr1_level_B.newData == 1) {
    /* '<S3>:1:25' silent = 0; */
    mixr1_level_DW.silent = 0.0;

    /* '<S3>:1:26' if status == 0 && dist > 0 && dist <= 2000 */
    if ((mixr1_level_B.status == 0) && (d > 0.0) && (d <= 2000.0)) {
      /* '<S3>:1:27' buf = [buf(2:3), double(dist)]; */
      mixr1_level_DW.buf[0] = mixr1_level_DW.buf[1];
      mixr1_level_DW.buf[1] = mixr1_level_DW.buf[2];
      mixr1_level_DW.buf[2] = d;

      /* '<S3>:1:28' nvalid = min(nvalid + 1, 3); */
      if (mixr1_level_DW.nvalid + 1.0 <= 3.0) {
        mixr1_level_DW.nvalid++;
      } else {
        mixr1_level_DW.nvalid = 3.0;
      }

      /* '<S3>:1:29' bad = 0; */
      mixr1_level_DW.bad = 0.0;

      /* '<S3>:1:30' lvl = max(0, zero - median(buf(4-nvalid:3)) - thickness); */
      switch (4 - (int32_T)(4.0 - mixr1_level_DW.nvalid)) {
       case 1:
        err = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        break;

       case 2:
        err = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        err += (mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid)] - err)
          / 2.0;
        break;

       default:
        err = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        tmp = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid)];
        if (err < tmp) {
          if (tmp < mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) +
              1]) {
            j2 = 1;
          } else if (err < mixr1_level_DW.buf[(int32_T)(4.0 -
                      mixr1_level_DW.nvalid) + 1]) {
            j2 = 2;
          } else {
            j2 = 0;
          }
        } else if (err < mixr1_level_DW.buf[(int32_T)(4.0 -
                    mixr1_level_DW.nvalid) + 1]) {
          j2 = 0;
        } else if (tmp < mixr1_level_DW.buf[(int32_T)(4.0 -
                    mixr1_level_DW.nvalid) + 1]) {
          j2 = 2;
        } else {
          j2 = 1;
        }

        err = mixr1_level_DW.buf[((int32_T)(4.0 - mixr1_level_DW.nvalid) + j2) -
          1];
        break;
      }

      err = (mixr1_level_P.Constant2_Value - err) -
        mixr1_level_P.Constant3_Value;
      if ((err <= 0.0) || rtIsNaN(err)) {
        mixr1_level_DW.lvl = 0.0;
      } else {
        mixr1_level_DW.lvl = err;
      }

      /* '<S3>:1:31' haveLvl = true; */
      mixr1_level_DW.haveLvl = true;
    } else {
      /* '<S3>:1:32' else */
      /* '<S3>:1:33' bad = bad + 1; */
      mixr1_level_DW.bad++;
    }

    /* '<S3>:1:35' else */
    /* '<S3>:1:36' silent = min(silent + 1, 1e6); */
  } else if (mixr1_level_DW.silent + 1.0 <= 1.0E+6) {
    mixr1_level_DW.silent++;
  } else {
    mixr1_level_DW.silent = 1.0E+6;
  }

  /* '<S3>:1:40' if cmd == 0 */
  if (fc_cmd == 0) {
    /* '<S3>:1:41' st = uint8(0); */
    mixr1_level_DW.st = 0U;

    /* '<S3>:1:42' holdMode = false; */
    mixr1_level_DW.holdMode = false;
  } else if ((fc_cmd != mixr1_level_DW.prevCmd) && ((mixr1_level_DW.st == 0) ||
              (mixr1_level_DW.st == 3) || (mixr1_level_DW.st == 4) ||
              (mixr1_level_DW.st == 10)) && (fc_cmd <= 4)) {
    /* '<S3>:1:43' elseif cmd ~= prevCmd && (st == 0 || st == 3 || st == 4 || st == 10) && (cmd >= 1 && cmd <= 4) */
    /* '<S3>:1:44' holdMode = (cmd == 4); */
    mixr1_level_DW.holdMode = (fc_cmd == 4);

    /* '<S3>:1:45' if cmd == 3 */
    switch (fc_cmd) {
     case 3U:
      /* '<S3>:1:46' st = uint8(5); */
      mixr1_level_DW.st = 5U;
      break;

     case 4U:
      /* '<S3>:1:47' elseif cmd == 4 */
      /* '<S3>:1:48' st = uint8(10); */
      mixr1_level_DW.st = 10U;
      break;

     default:
      /* '<S3>:1:49' else */
      /* '<S3>:1:50' st = cmd; */
      mixr1_level_DW.st = fc_cmd;
      break;
    }

    /* '<S3>:1:52' nvalid = 0; */
    mixr1_level_DW.nvalid = 0.0;

    /* '<S3>:1:52' haveLvl = false; */
    mixr1_level_DW.haveLvl = false;

    /* '<S3>:1:52' bad = 0; */
    mixr1_level_DW.bad = 0.0;

    /* '<S3>:1:52' silent = 0; */
    mixr1_level_DW.silent = 0.0;

    /* '<S3>:1:52' runSteps = 0; */
    mixr1_level_DW.runSteps = 0.0;

    /* '<S3>:1:52' outSteps = 0; */
    mixr1_level_DW.outSteps = 0.0;

    /* '<S3>:1:52' trims = 0; */
    mixr1_level_DW.trims = 0.0;
  }

  /* '<S3>:1:54' prevCmd = cmd; */
  mixr1_level_DW.prevCmd = fc_cmd;

  /* '<S3>:1:57' if st ~= prevSt */
  if (mixr1_level_DW.st != mixr1_level_DW.prevSt) {
    /* '<S3>:1:58' runSteps = 0; */
    mixr1_level_DW.runSteps = 0.0;
  }

  /* '<S3>:1:60' prevSt = st; */
  mixr1_level_DW.prevSt = mixr1_level_DW.st;

  /* '<S3>:1:63' active = (st == 1 || st == 2 || st == 5 || st == 6 || st == 7 || st == 8 || st == 10); */
  /* '<S3>:1:64' if active */
  if ((mixr1_level_DW.st == 1) || (mixr1_level_DW.st == 2) || (mixr1_level_DW.st
       == 5) || (mixr1_level_DW.st == 6) || (mixr1_level_DW.st == 7) ||
      (mixr1_level_DW.st == 8) || (mixr1_level_DW.st == 10)) {
    /* '<S3>:1:65' runSteps = runSteps + 1; */
    mixr1_level_DW.runSteps++;

    /* '<S3>:1:66' if bad >= MAX_BAD || silent >= MAX_SILENT || ... */
    /* '<S3>:1:67'             (st ~= 6 && st ~= 10 && runSteps >= MAX_RUN) */
    if ((mixr1_level_DW.bad >= 10.0) || (mixr1_level_DW.silent >= 40.0) ||
        ((mixr1_level_DW.st != 6) && (mixr1_level_DW.st != 10) &&
         (mixr1_level_DW.runSteps >= 4800.0))) {
      /* '<S3>:1:68' st = uint8(9); */
      mixr1_level_DW.st = 9U;
    } else if (mixr1_level_DW.haveLvl) {
      /* '<S3>:1:69' elseif haveLvl */
      /* '<S3>:1:70' if st == 1 */
      switch (mixr1_level_DW.st) {
       case 1U:
        /* '<S3>:1:71' if lvl >= target */
        if (mixr1_level_DW.lvl >= fc_target) {
          /* '<S3>:1:71' , */
          /* '<S3>:1:71' st = uint8(3); */
          mixr1_level_DW.st = 3U;
        }
        break;

       case 2U:
        /* '<S3>:1:72' elseif st == 2 */
        /* '<S3>:1:73' if lvl <= max(drainTo, EMPTY_MM) */
        if (fc_drainTo >= 2.0) {
          err = fc_drainTo;
        } else {
          err = 2.0;
        }

        if (mixr1_level_DW.lvl <= err) {
          /* '<S3>:1:73' , */
          /* '<S3>:1:73' st = uint8(4); */
          mixr1_level_DW.st = 4U;
        }
        break;

       case 5U:
        /* '<S3>:1:74' elseif st == 5 */
        /* '<S3>:1:75' if lvl >= target + max(overshoot, 0) */
        if (fc_overshoot >= 0.0) {
          err = fc_overshoot;
        } else {
          err = 0.0;
        }

        if (mixr1_level_DW.lvl >= fc_target + err) {
          /* '<S3>:1:75' , */
          /* '<S3>:1:75' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 6U:
        /* '<S3>:1:76' elseif st == 6 */
        /* '<S3>:1:77' if runSteps >= round(settle / DT) */
        if (mixr1_level_DW.runSteps >= rt_roundd_snf(fc_settle / 0.05)) {
          /* '<S3>:1:78' err = lvl - target; */
          err = mixr1_level_DW.lvl - fc_target;

          /* '<S3>:1:79' if abs(err) <= tol */
          if (fabs(err) <= fc_tol) {
            /* '<S3>:1:80' if holdMode */
            if (mixr1_level_DW.holdMode) {
              /* '<S3>:1:81' st = uint8(10); */
              mixr1_level_DW.st = 10U;

              /* '<S3>:1:81' outSteps = 0; */
              mixr1_level_DW.outSteps = 0.0;

              /* '<S3>:1:81' trims = 0; */
              mixr1_level_DW.trims = 0.0;
            } else {
              /* '<S3>:1:82' else */
              /* '<S3>:1:83' st = uint8(3); */
              mixr1_level_DW.st = 3U;
            }
          } else if (mixr1_level_DW.trims >= 5.0) {
            /* '<S3>:1:85' elseif trims >= MAX_TRIM */
            /* '<S3>:1:86' st = uint8(9); */
            mixr1_level_DW.st = 9U;
          } else if (err > 0.0) {
            /* '<S3>:1:87' elseif err > 0 */
            /* '<S3>:1:88' st = uint8(7); */
            mixr1_level_DW.st = 7U;

            /* '<S3>:1:88' trims = trims + 1; */
            mixr1_level_DW.trims++;
          } else {
            /* '<S3>:1:89' else */
            /* '<S3>:1:90' st = uint8(8); */
            mixr1_level_DW.st = 8U;

            /* '<S3>:1:90' trims = trims + 1; */
            mixr1_level_DW.trims++;
          }
        }
        break;

       case 7U:
        /* '<S3>:1:93' elseif st == 7 */
        /* '<S3>:1:94' if lvl <= target */
        if (mixr1_level_DW.lvl <= fc_target) {
          /* '<S3>:1:94' , */
          /* '<S3>:1:94' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 8U:
        /* '<S3>:1:95' elseif st == 8 */
        /* '<S3>:1:96' if lvl >= target */
        if (mixr1_level_DW.lvl >= fc_target) {
          /* '<S3>:1:96' , */
          /* '<S3>:1:96' st = uint8(6); */
          mixr1_level_DW.st = 6U;
        }
        break;

       case 10U:
        /* '<S3>:1:97' elseif st == 10 */
        /* '<S3>:1:98' if abs(lvl - target) > tol */
        if (fabs(mixr1_level_DW.lvl - fc_target) > fc_tol) {
          /* '<S3>:1:99' outSteps = outSteps + 1; */
          mixr1_level_DW.outSteps++;
        } else {
          /* '<S3>:1:100' else */
          /* '<S3>:1:101' outSteps = 0; */
          mixr1_level_DW.outSteps = 0.0;
        }

        /* '<S3>:1:103' if outSteps >= round(settle / DT) */
        if (mixr1_level_DW.outSteps >= rt_roundd_snf(fc_settle / 0.05)) {
          /* '<S3>:1:104' outSteps = 0; */
          mixr1_level_DW.outSteps = 0.0;

          /* '<S3>:1:105' trims = trims + 1; */
          mixr1_level_DW.trims++;

          /* '<S3>:1:106' if lvl > target */
          if (mixr1_level_DW.lvl > fc_target) {
            /* '<S3>:1:107' st = uint8(7); */
            mixr1_level_DW.st = 7U;
          } else {
            /* '<S3>:1:108' else */
            /* '<S3>:1:109' st = uint8(8); */
            mixr1_level_DW.st = 8U;
          }
        }
        break;
      }
    }
  }

  /* '<S3>:1:117' pumpOn   = uint8((st == 1 || st == 5 || st == 8) && haveLvl); */
  /* '<S3>:1:118' valveOn  = uint8((st == 2 || st == 7) && haveLvl); */
  /* '<S3>:1:119' pumpPwm  = uint16(min(PWM_RANGE, max(0, round(pumpV  / V_MAX * PWM_RANGE)))); */
  err = rt_roundd_snf(fc_pumpV / 12.0 * 1024.0);
  if ((err <= 0.0) || rtIsNaN(err)) {
    err = 0.0;
  }

  if (err >= 1024.0) {
    mixr1_level_B.pumpPwm = 1024U;
  } else {
    mixr1_level_B.pumpPwm = (uint16_T)err;
  }

  /* '<S3>:1:120' valvePwm = uint16(min(PWM_RANGE, max(0, round(valveV / V_MAX * PWM_RANGE)))); */
  /* '<S3>:1:121' level    = lvl; */
  mixr1_level_B.level = mixr1_level_DW.lvl;

  /* '<S3>:1:122' state    = st; */
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

  /* MATLAB Function: '<Root>/fluid_ctrl' incorporates:
   *  Constant: '<Root>/Constant6'
   */
  /* '<S1>:1:16' coder.ceval('act_step', pumpOn, pumpPwm, valveOn, valvePwm); */
  err = rt_roundd_snf(fc_valveV / 12.0 * 1024.0);
  if ((err <= 0.0) || rtIsNaN(err)) {
    err = 0.0;
  }

  if (err >= 1024.0) {
    j2 = 1024;
  } else {
    j2 = (int32_T)err;
  }

  /* MATLAB Function: '<Root>/Actuators' incorporates:
   *  MATLAB Function: '<Root>/fluid_ctrl'
   */
  act_step((uint8_T)(((mixr1_level_DW.st == 1) || (mixr1_level_DW.st == 5) ||
                      (mixr1_level_DW.st == 8)) && mixr1_level_DW.haveLvl),
           mixr1_level_B.pumpPwm, (uint8_T)(((mixr1_level_DW.st == 2) ||
             (mixr1_level_DW.st == 7)) && mixr1_level_DW.haveLvl), (uint16_T)j2);

  /* MATLAB Function: '<Root>/pack_log' incorporates:
   *  Constant: '<Root>/fc_mark'
   */
  /* MATLAB Function 'pack_log': '<S4>:1' */
  /* '<S4>:1:2' y = [double(dist), double(status), double(newData), level, double(state), mark]; */
  mixr1_level_B.y[0] = d;
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
  mixr1_level_M->Sizes.checksums[0] = (1077999554U);
  mixr1_level_M->Sizes.checksums[1] = (2320269882U);
  mixr1_level_M->Sizes.checksums[2] = (874467310U);
  mixr1_level_M->Sizes.checksums[3] = (1541293678U);

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
  /* '<S3>:1:18' st = uint8(0); */
  mixr1_level_DW.st = 0U;

  /* '<S3>:1:18' prevSt = uint8(0); */
  mixr1_level_DW.prevSt = 0U;

  /* '<S3>:1:18' prevCmd = uint8(0); */
  mixr1_level_DW.prevCmd = 0U;

  /* '<S3>:1:19' buf = zeros(1,3); */
  mixr1_level_DW.buf[0] = 0.0;
  mixr1_level_DW.buf[1] = 0.0;
  mixr1_level_DW.buf[2] = 0.0;

  /* '<S3>:1:19' nvalid = 0; */
  mixr1_level_DW.nvalid = 0.0;

  /* '<S3>:1:19' bad = 0; */
  mixr1_level_DW.bad = 0.0;

  /* '<S3>:1:19' silent = 0; */
  mixr1_level_DW.silent = 0.0;

  /* '<S3>:1:19' runSteps = 0; */
  mixr1_level_DW.runSteps = 0.0;

  /* '<S3>:1:19' outSteps = 0; */
  mixr1_level_DW.outSteps = 0.0;

  /* '<S3>:1:19' trims = 0; */
  mixr1_level_DW.trims = 0.0;

  /* '<S3>:1:20' lvl = 0; */
  mixr1_level_DW.lvl = 0.0;

  /* '<S3>:1:20' haveLvl = false; */
  mixr1_level_DW.haveLvl = false;

  /* '<S3>:1:20' holdMode = false; */
  mixr1_level_DW.holdMode = false;

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

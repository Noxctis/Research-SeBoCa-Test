/*
 * mixr1_level.c
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

#include "mixr1_level.h"
#include "tof_wrapper.h"
#include "act_wrapper.h"
#include "rt_nonfinite.h"
#include "mixr1_level_private.h"
#include "rtwtypes.h"
#include <string.h>
#include <math.h>

/* Exported block parameters */
real_T fc_pumpV = 12.0;                /* Variable: fc_pumpV
                                        * Referenced by: '<Root>/Constant4'
                                        */
real_T fc_target = 250.0;              /* Variable: fc_target
                                        * Referenced by: '<Root>/Constant1'
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
  real_T tmp;
  real_T y;
  int32_T j2;

  /* MATLAB Function: '<Root>/tof_read' */
  /* MATLAB Function 'tof_read': '<S4>:1' */
  /* '<S4>:1:2' coder.extrinsic('which', 'fileparts'); */
  /* '<S4>:1:3' dist    = uint16(0); */
  /* '<S4>:1:4' status  = uint8(255); */
  /* '<S4>:1:5' newData = uint8(0); */
  /* '<S4>:1:8' if isempty(k) */
  /* '<S4>:1:13' if coder.target('Sfun') */
  /* '<S4>:1:18' else */
  /* '<S4>:1:19' srcDir = coder.const(fileparts(which('tof_wrapper.c'))); */
  /* '<S4>:1:20' coder.cinclude('tof_wrapper.h'); */
  /* '<S4>:1:21' coder.updateBuildInfo('addIncludePaths', srcDir); */
  /* '<S4>:1:22' coder.updateBuildInfo('addSourcePaths',  srcDir); */
  /* '<S4>:1:23' coder.updateBuildInfo('addSourceFiles', 'tof_wrapper.c'); */
  /* '<S4>:1:24' coder.updateBuildInfo('addSourceFiles', 'VL53L4CD_api.c'); */
  /* '<S4>:1:25' coder.updateBuildInfo('addSourceFiles', 'platform.c'); */
  /* '<S4>:1:27' if ~started */
  if (!mixr1_level_DW.started) {
    /* '<S4>:1:28' coder.ceval('tof_init', int16(-26), uint16(200)); */
    tof_init(-26, 200);

    /* '<S4>:1:29' started = true; */
    mixr1_level_DW.started = true;
  }

  /* '<S4>:1:31' coder.ceval('tof_step', coder.wref(dist), coder.wref(status), coder.wref(newData)); */
  tof_step(&mixr1_level_B.dist, &mixr1_level_B.status, &mixr1_level_B.newData);

  /* End of MATLAB Function: '<Root>/tof_read' */

  /* MATLAB Function: '<Root>/fluid_ctrl' incorporates:
   *  Constant: '<Root>/Constant'
   *  Constant: '<Root>/Constant1'
   *  Constant: '<Root>/Constant2'
   *  Constant: '<Root>/Constant3'
   */
  /* MATLAB Function 'fluid_ctrl': '<S2>:1' */
  /* '<S2>:1:4' MAX_BAD    = 10; */
  /* '<S2>:1:5' MAX_SILENT = 40; */
  /* '<S2>:1:6' MAX_RUN    = 2400; */
  /* '<S2>:1:7' V_MAX      = 12.0; */
  /* '<S2>:1:8' PWM_RANGE  = 1024; */
  /* '<S2>:1:11' if isempty(st) */
  /* '<S2>:1:18' if newData == 1 */
  if (mixr1_level_B.newData == 1) {
    /* '<S2>:1:19' silent = 0; */
    mixr1_level_DW.silent = 0.0;

    /* '<S2>:1:20' if status == 0 && dist > 0 && dist <= 2000 */
    if ((mixr1_level_B.status == 0) && (mixr1_level_B.dist > 0) &&
        (mixr1_level_B.dist <= 2000)) {
      /* '<S2>:1:21' buf = [buf(2:3), double(dist)]; */
      mixr1_level_DW.buf[0] = mixr1_level_DW.buf[1];
      mixr1_level_DW.buf[1] = mixr1_level_DW.buf[2];
      mixr1_level_DW.buf[2] = mixr1_level_B.dist;

      /* '<S2>:1:22' nvalid = min(nvalid + 1, 3); */
      if (mixr1_level_DW.nvalid + 1.0 <= 3.0) {
        mixr1_level_DW.nvalid++;
      } else {
        mixr1_level_DW.nvalid = 3.0;
      }

      /* '<S2>:1:23' bad = 0; */
      mixr1_level_DW.bad = 0.0;

      /* '<S2>:1:24' lvl = max(0, zero - median(buf(4-nvalid:3)) - thickness); */
      switch (4 - (int32_T)(4.0 - mixr1_level_DW.nvalid)) {
       case 1:
        y = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        break;

       case 2:
        y = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        y += (mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid)] - y) /
          2.0;
        break;

       default:
        y = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) - 1];
        tmp = mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid)];
        if (y < tmp) {
          if (tmp < mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid) +
              1]) {
            j2 = 1;
          } else if (y < mixr1_level_DW.buf[(int32_T)(4.0 -
                      mixr1_level_DW.nvalid) + 1]) {
            j2 = 2;
          } else {
            j2 = 0;
          }
        } else if (y < mixr1_level_DW.buf[(int32_T)(4.0 - mixr1_level_DW.nvalid)
                   + 1]) {
          j2 = 0;
        } else if (tmp < mixr1_level_DW.buf[(int32_T)(4.0 -
                    mixr1_level_DW.nvalid) + 1]) {
          j2 = 2;
        } else {
          j2 = 1;
        }

        y = mixr1_level_DW.buf[((int32_T)(4.0 - mixr1_level_DW.nvalid) + j2) - 1];
        break;
      }

      y = (mixr1_level_P.Constant2_Value - y) - mixr1_level_P.Constant3_Value;
      if ((y <= 0.0) || rtIsNaN(y)) {
        mixr1_level_DW.lvl = 0.0;
      } else {
        mixr1_level_DW.lvl = y;
      }

      /* '<S2>:1:25' haveLvl = true; */
      mixr1_level_DW.haveLvl = true;
    } else {
      /* '<S2>:1:26' else */
      /* '<S2>:1:27' bad = bad + 1; */
      mixr1_level_DW.bad++;
    }

    /* '<S2>:1:29' else */
    /* '<S2>:1:30' silent = min(silent + 1, 1e6); */
  } else if (mixr1_level_DW.silent + 1.0 <= 1.0E+6) {
    mixr1_level_DW.silent++;
  } else {
    mixr1_level_DW.silent = 1.0E+6;
  }

  /* '<S2>:1:34' if cmd == 0 */
  if (fc_cmd == 0) {
    /* '<S2>:1:35' st = uint8(0); */
    mixr1_level_DW.st = 0U;
  } else if ((fc_cmd != mixr1_level_DW.prevCmd) && ((mixr1_level_DW.st == 0) ||
              (mixr1_level_DW.st == 3)) && (fc_cmd == 1)) {
    /* '<S2>:1:36' elseif cmd ~= prevCmd && (st == 0 || st == 3) && cmd == 1 */
    /* '<S2>:1:37' st = uint8(1); */
    mixr1_level_DW.st = 1U;

    /* '<S2>:1:38' nvalid = 0; */
    mixr1_level_DW.nvalid = 0.0;

    /* '<S2>:1:38' haveLvl = false; */
    mixr1_level_DW.haveLvl = false;

    /* '<S2>:1:38' bad = 0; */
    mixr1_level_DW.bad = 0.0;

    /* '<S2>:1:38' silent = 0; */
    mixr1_level_DW.silent = 0.0;

    /* '<S2>:1:38' runSteps = 0; */
    mixr1_level_DW.runSteps = 0.0;
  }

  /* '<S2>:1:40' prevCmd = cmd; */
  mixr1_level_DW.prevCmd = fc_cmd;

  /* '<S2>:1:43' if st == 1 */
  if (mixr1_level_DW.st == 1) {
    /* '<S2>:1:44' runSteps = runSteps + 1; */
    mixr1_level_DW.runSteps++;

    /* '<S2>:1:45' if bad >= MAX_BAD || silent >= MAX_SILENT || runSteps >= MAX_RUN */
    if ((mixr1_level_DW.bad >= 10.0) || (mixr1_level_DW.silent >= 40.0) ||
        (mixr1_level_DW.runSteps >= 2400.0)) {
      /* '<S2>:1:46' st = uint8(9); */
      mixr1_level_DW.st = 9U;
    } else if (mixr1_level_DW.haveLvl && (mixr1_level_DW.lvl >= fc_target)) {
      /* '<S2>:1:47' elseif haveLvl && lvl >= target */
      /* '<S2>:1:48' st = uint8(3); */
      mixr1_level_DW.st = 3U;
    }
  }

  /* '<S2>:1:53' pumpOn  = uint8(st == 1 && haveLvl); */
  /* '<S2>:1:54' pumpPwm = uint16(min(PWM_RANGE, max(0, round(pumpV / V_MAX * PWM_RANGE)))); */
  /* '<S2>:1:55' level   = lvl; */
  mixr1_level_B.level = mixr1_level_DW.lvl;

  /* '<S2>:1:56' state   = st; */
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
   *  Constant: '<Root>/Constant4'
   */
  /* '<S1>:1:16' coder.ceval('act_step', pumpOn, pumpPwm); */
  y = rt_roundd_snf(fc_pumpV / 12.0 * 1024.0);
  if ((y <= 0.0) || rtIsNaN(y)) {
    y = 0.0;
  }

  if (y >= 1024.0) {
    j2 = 1024;
  } else {
    j2 = (int32_T)y;
  }

  /* MATLAB Function: '<Root>/Actuators' incorporates:
   *  MATLAB Function: '<Root>/fluid_ctrl'
   */
  act_step((uint8_T)((mixr1_level_DW.st == 1) && mixr1_level_DW.haveLvl),
           (uint16_T)j2);

  /* MATLAB Function: '<Root>/pack_log' incorporates:
   *  Constant: '<Root>/fc_mark'
   */
  /* MATLAB Function 'pack_log': '<S3>:1' */
  /* '<S3>:1:2' y = [double(dist), double(status), double(newData), level, double(state), mark]; */
  mixr1_level_B.y[0] = mixr1_level_B.dist;
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
  mixr1_level_M->Sizes.checksums[0] = (3853299069U);
  mixr1_level_M->Sizes.checksums[1] = (2920541419U);
  mixr1_level_M->Sizes.checksums[2] = (1461062194U);
  mixr1_level_M->Sizes.checksums[3] = (3450946366U);

  {
    static const sysRanDType rtAlwaysEnabled = SUBSYS_RAN_BC_ENABLE;
    static RTWExtModeInfo rt_ExtModeInfo;
    static const sysRanDType *systemRan[5];
    mixr1_level_M->extModeInfo = (&rt_ExtModeInfo);
    rteiSetSubSystemActiveVectorAddresses(&rt_ExtModeInfo, systemRan);
    systemRan[0] = &rtAlwaysEnabled;
    systemRan[1] = &rtAlwaysEnabled;
    systemRan[2] = &rtAlwaysEnabled;
    systemRan[3] = &rtAlwaysEnabled;
    systemRan[4] = &rtAlwaysEnabled;
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

  /* SystemInitialize for MATLAB Function: '<Root>/tof_read' */
  /* '<S4>:1:9' k = uint16(0); */
  /* '<S4>:1:10' started = false; */
  mixr1_level_DW.started = false;

  /* SystemInitialize for MATLAB Function: '<Root>/fluid_ctrl' */
  /* '<S2>:1:12' st = uint8(0); */
  mixr1_level_DW.st = 0U;

  /* '<S2>:1:12' prevCmd = uint8(0); */
  mixr1_level_DW.prevCmd = 0U;

  /* '<S2>:1:13' buf = zeros(1,3); */
  mixr1_level_DW.buf[0] = 0.0;
  mixr1_level_DW.buf[1] = 0.0;
  mixr1_level_DW.buf[2] = 0.0;

  /* '<S2>:1:13' nvalid = 0; */
  mixr1_level_DW.nvalid = 0.0;

  /* '<S2>:1:13' bad = 0; */
  mixr1_level_DW.bad = 0.0;

  /* '<S2>:1:13' silent = 0; */
  mixr1_level_DW.silent = 0.0;

  /* '<S2>:1:13' runSteps = 0; */
  mixr1_level_DW.runSteps = 0.0;

  /* '<S2>:1:14' lvl = 0; */
  mixr1_level_DW.lvl = 0.0;

  /* '<S2>:1:14' haveLvl = false; */
  mixr1_level_DW.haveLvl = false;

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

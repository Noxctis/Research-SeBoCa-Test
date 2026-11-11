/*
 * mixr_level_test.h
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "mixr_level_test".
 *
 * Model version              : 1.18
 * Simulink Coder version : 26.1 (R2026a) 20-Nov-2025
 * C source code generated on : Mon Nov  9 16:35:13 2026
 *
 * Target selection: ert.tlc
 * Embedded hardware selection: ARM Compatible->ARM Cortex-A (64-bit)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#ifndef mixr_level_test_h_
#define mixr_level_test_h_
#ifndef mixr_level_test_COMMON_INCLUDES_
#define mixr_level_test_COMMON_INCLUDES_
#include "rtwtypes.h"
#include "rtw_extmode.h"
#include "sysran_types.h"
#include "rtw_continuous.h"
#include "rtw_solver.h"
#endif                                 /* mixr_level_test_COMMON_INCLUDES_ */

#include "mixr_level_test_types.h"
#include "rt_nonfinite.h"
#include "rtGetInf.h"
#include "rtGetNaN.h"
#include <string.h>
#include <stddef.h>

/* Macros for accessing real-time model data structure */
#ifndef rtmGetFinalTime
#define rtmGetFinalTime(rtm)           ((rtm)->Timing.tFinal)
#endif

#ifndef rtmGetRTWExtModeInfo
#define rtmGetRTWExtModeInfo(rtm)      ((rtm)->extModeInfo)
#endif

#ifndef rtmGetErrorStatus
#define rtmGetErrorStatus(rtm)         ((rtm)->errorStatus)
#endif

#ifndef rtmSetErrorStatus
#define rtmSetErrorStatus(rtm, val)    ((rtm)->errorStatus = (val))
#endif

#ifndef rtmGetStopRequested
#define rtmGetStopRequested(rtm)       ((rtm)->Timing.stopRequestedFlag)
#endif

#ifndef rtmSetStopRequested
#define rtmSetStopRequested(rtm, val)  ((rtm)->Timing.stopRequestedFlag = (val))
#endif

#ifndef rtmGetStopRequestedPtr
#define rtmGetStopRequestedPtr(rtm)    (&((rtm)->Timing.stopRequestedFlag))
#endif

#ifndef rtmGetTFinal
#define rtmGetTFinal(rtm)              ((rtm)->Timing.tFinal)
#endif

#ifndef rtmGetTPtr
#define rtmGetTPtr(rtm)                (&)
#endif

/* Block signals (default storage) */
typedef struct {
  real_T y[6];                         /* '<Root>/pack_log' */
  real_T level;                        /* '<Root>/fluid_ctrl' */
  real_T viz[6];                       /* '<Root>/fluid_ctrl' */
  uint16_T dist;                       /* '<S2>/tof_read' */
  uint8_T state;                       /* '<Root>/fluid_ctrl' */
  uint8_T reason;                      /* '<Root>/fluid_ctrl' */
  uint8_T status;                      /* '<S2>/tof_read' */
  uint8_T newData;                     /* '<S2>/tof_read' */
} B_mixr_level_test_T;

/* Block states (default storage) for system '<Root>' */
typedef struct {
  real_T prevSeq;                      /* '<Root>/fluid_ctrl' */
  real_T buf[3];                       /* '<Root>/fluid_ctrl' */
  real_T nvalid;                       /* '<Root>/fluid_ctrl' */
  real_T bad;                          /* '<Root>/fluid_ctrl' */
  real_T silent;                       /* '<Root>/fluid_ctrl' */
  real_T runSteps;                     /* '<Root>/fluid_ctrl' */
  real_T outSteps;                     /* '<Root>/fluid_ctrl' */
  real_T fails;                        /* '<Root>/fluid_ctrl' */
  real_T curScale;                     /* '<Root>/fluid_ctrl' */
  real_T lvl;                          /* '<Root>/fluid_ctrl' */
  real_T gap;                          /* '<Root>/fluid_ctrl' */
  struct {
    void *LoggedData[2];
  } LevelScope_PWORK;                  /* '<Root>/LevelScope' */

  uint8_T st;                          /* '<Root>/fluid_ctrl' */
  uint8_T prevSt;                      /* '<Root>/fluid_ctrl' */
  uint8_T prevCmd;                     /* '<Root>/fluid_ctrl' */
  uint8_T why;                         /* '<Root>/fluid_ctrl' */
  uint8_T pending;                     /* '<Root>/fluid_ctrl' */
  boolean_T doneDoubleBufferReInit;    /* '<Root>/pack_log' */
  boolean_T doneDoubleBufferReInit_f;  /* '<Root>/fluid_ctrl' */
  boolean_T haveLvl;                   /* '<Root>/fluid_ctrl' */
  boolean_T ctlStarted;                /* '<Root>/fluid_ctrl' */
  boolean_T doneDoubleBufferReInit_m;  /* '<S2>/tof_read1' */
  boolean_T doneDoubleBufferReInit_ma; /* '<S2>/tof_read' */
  boolean_T started;                   /* '<S2>/tof_read' */
  boolean_T doneDoubleBufferReInit_e;  /* '<Root>/Actuators' */
  boolean_T started_l;                 /* '<Root>/Actuators' */
} DW_mixr_level_test_T;

/* Parameters (default storage) */
struct P_mixr_level_test_T_ {
  real_T fc_mark_Value;                /* Expression: 0
                                        * Referenced by: '<Root>/fc_mark'
                                        */
};

/* Real-time Model Data Structure */
struct tag_RTM_mixr_level_test_T {
  const char_T *errorStatus;
  RTWExtModeInfo *extModeInfo;

  /*
   * Sizes:
   * The following substructure contains sizes information
   * for many of the model attributes such as inputs, outputs,
   * dwork, sample times, etc.
   */
  struct {
    uint32_T checksums[4];
  } Sizes;

  /*
   * SpecialInfo:
   * The following substructure contains special information
   * related to other components that are dependent on RTW.
   */
  struct {
    const void *mappingInfo;
  } SpecialInfo;

  /*
   * Timing:
   * The following substructure contains information regarding
   * the timing information for the model.
   */
  struct {
    uint32_T clockTick0;
    time_T tFinal;
    boolean_T stopRequestedFlag;
  } Timing;
};

/* Block parameters (default storage) */
extern P_mixr_level_test_T mixr_level_test_P;

/* Block signals (default storage) */
extern B_mixr_level_test_T mixr_level_test_B;

/* Block states (default storage) */
extern DW_mixr_level_test_T mixr_level_test_DW;

/*
 * Exported Global Parameters
 *
 * Note: Exported global parameters are tunable parameters with an exported
 * global storage class designation.  Code generation will declare the memory for
 * these parameters and exports their symbols.
 *
 */
extern real_T fc_defaults[10];         /* Variable: fc_defaults
                                        * Referenced by: '<Root>/fc_defaults_const'
                                        */
extern real_T fc_tofGain;              /* Variable: fc_tofGain
                                        * Referenced by: '<S2>/Constant10'
                                        */
extern real_T fc_tofIntercept;         /* Variable: fc_tofIntercept
                                        * Referenced by: '<S2>/Constant12'
                                        */

/* Model entry point functions */
extern void mixr_level_test_initialize(void);
extern void mixr_level_test_step(void);
extern void mixr_level_test_terminate(void);

/* Real-time Model object */
extern RT_MODEL_mixr_level_test_T *const mixr_level_test_M;
extern volatile boolean_T stopRequested;
extern volatile boolean_T runModel;

/*-
 * The generated code includes comments that allow you to trace directly
 * back to the appropriate location in the model.  The basic format
 * is <system>/block_name, where system is the system number (uniquely
 * assigned by Simulink) and block_name is the name of the block.
 *
 * Use the MATLAB hilite_system command to trace the generated code back
 * to the model.  For example,
 *
 * hilite_system('<S3>')    - opens system 3
 * hilite_system('<S3>/Kp') - opens and selects block Kp which resides in S3
 *
 * Here is the system hierarchy for this model
 *
 * '<Root>' : 'mixr_level_test'
 * '<S1>'   : 'mixr_level_test/Actuators'
 * '<S2>'   : 'mixr_level_test/ToF_Calibrated'
 * '<S3>'   : 'mixr_level_test/fluid_ctrl'
 * '<S4>'   : 'mixr_level_test/pack_log'
 * '<S5>'   : 'mixr_level_test/ToF_Calibrated/tof_read'
 * '<S6>'   : 'mixr_level_test/ToF_Calibrated/tof_read1'
 */
#endif                                 /* mixr_level_test_h_ */

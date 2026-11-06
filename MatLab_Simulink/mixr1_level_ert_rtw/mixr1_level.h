/*
 * mixr1_level.h
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

#ifndef mixr1_level_h_
#define mixr1_level_h_
#ifndef mixr1_level_COMMON_INCLUDES_
#define mixr1_level_COMMON_INCLUDES_
#include "rtwtypes.h"
#include "rtw_extmode.h"
#include "sysran_types.h"
#include "rtw_continuous.h"
#include "rtw_solver.h"
#endif                                 /* mixr1_level_COMMON_INCLUDES_ */

#include "mixr1_level_types.h"
#include "rtGetInf.h"
#include "rtGetNaN.h"
#include <string.h>
#include "rt_nonfinite.h"
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
  real_T d;                            /* '<S2>/tof_read1' */
  uint16_T pumpPwm;                    /* '<Root>/fluid_ctrl' */
  uint16_T dist;                       /* '<S2>/tof_read' */
  uint8_T state;                       /* '<Root>/fluid_ctrl' */
  uint8_T status;                      /* '<S2>/tof_read' */
  uint8_T newData;                     /* '<S2>/tof_read' */
} B_mixr1_level_T;

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
  uint8_T st;                          /* '<Root>/fluid_ctrl' */
  uint8_T prevSt;                      /* '<Root>/fluid_ctrl' */
  uint8_T prevCmd;                     /* '<Root>/fluid_ctrl' */
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
} DW_mixr1_level_T;

/* Parameters (default storage) */
struct P_mixr1_level_T_ {
  real_T Constant2_Value;              /* Expression: 389
                                        * Referenced by: '<Root>/Constant2'
                                        */
  real_T Constant3_Value;              /* Expression: 0
                                        * Referenced by: '<Root>/Constant3'
                                        */
  real_T fc_mark_Value;                /* Expression: 0
                                        * Referenced by: '<Root>/fc_mark'
                                        */
};

/* Real-time Model Data Structure */
struct tag_RTM_mixr1_level_T {
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
extern P_mixr1_level_T mixr1_level_P;

/* Block signals (default storage) */
extern B_mixr1_level_T mixr1_level_B;

/* Block states (default storage) */
extern DW_mixr1_level_T mixr1_level_DW;

/*
 * Exported Global Parameters
 *
 * Note: Exported global parameters are tunable parameters with an exported
 * global storage class designation.  Code generation will declare the memory for
 * these parameters and exports their symbols.
 *
 */
extern real_T fc_drainTo;              /* Variable: fc_drainTo
                                        * Referenced by: '<Root>/Constant5'
                                        */
extern real_T fc_overshoot;            /* Variable: fc_overshoot
                                        * Referenced by: '<Root>/Constant7'
                                        */
extern real_T fc_pumpV;                /* Variable: fc_pumpV
                                        * Referenced by: '<Root>/Constant4'
                                        */
extern real_T fc_settle;               /* Variable: fc_settle
                                        * Referenced by: '<Root>/Constant9'
                                        */
extern real_T fc_target;               /* Variable: fc_target
                                        * Referenced by: '<Root>/Constant1'
                                        */
extern real_T fc_tofGain;              /* Variable: fc_tofGain
                                        * Referenced by: '<S2>/Constant10'
                                        */
extern real_T fc_tofIntercept;         /* Variable: fc_tofIntercept
                                        * Referenced by: '<S2>/Constant12'
                                        */
extern real_T fc_tol;                  /* Variable: fc_tol
                                        * Referenced by: '<Root>/Constant8'
                                        */
extern real_T fc_valveV;               /* Variable: fc_valveV
                                        * Referenced by: '<Root>/Constant6'
                                        */
extern uint8_T fc_cmd;                 /* Variable: fc_cmd
                                        * Referenced by: '<Root>/Constant'
                                        */

/* Model entry point functions */
extern void mixr1_level_initialize(void);
extern void mixr1_level_step(void);
extern void mixr1_level_terminate(void);

/* Real-time Model object */
extern RT_MODEL_mixr1_level_T *const mixr1_level_M;
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
 * '<Root>' : 'mixr1_level'
 * '<S1>'   : 'mixr1_level/Actuators'
 * '<S2>'   : 'mixr1_level/ToF_Calibrated'
 * '<S3>'   : 'mixr1_level/fluid_ctrl'
 * '<S4>'   : 'mixr1_level/pack_log'
 * '<S5>'   : 'mixr1_level/ToF_Calibrated/tof_read'
 * '<S6>'   : 'mixr1_level/ToF_Calibrated/tof_read1'
 */
#endif                                 /* mixr1_level_h_ */

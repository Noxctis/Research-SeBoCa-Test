/*
 * mixr1_v2_dev.h
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

#ifndef mixr1_v2_dev_h_
#define mixr1_v2_dev_h_
#ifndef mixr1_v2_dev_COMMON_INCLUDES_
#define mixr1_v2_dev_COMMON_INCLUDES_
#include "rtwtypes.h"
#include "rtw_extmode.h"
#include "sysran_types.h"
#include "rtw_continuous.h"
#include "rtw_solver.h"
#include "ext_mode.h"
#endif                                 /* mixr1_v2_dev_COMMON_INCLUDES_ */

#include "mixr1_v2_dev_types.h"
#include <string.h>
#include "rt_nonfinite.h"
#include <stddef.h>

/* Macros for accessing real-time model data structure */
#ifndef rtmGetContStateDisabled
#define rtmGetContStateDisabled(rtm)   ((rtm)->contStateDisabled)
#endif

#ifndef rtmSetContStateDisabled
#define rtmSetContStateDisabled(rtm, val) ((rtm)->contStateDisabled = (val))
#endif

#ifndef rtmGetContStates
#define rtmGetContStates(rtm)          ((rtm)->contStates)
#endif

#ifndef rtmSetContStates
#define rtmSetContStates(rtm, val)     ((rtm)->contStates = (val))
#endif

#ifndef rtmGetContTimeOutputInconsistentWithStateAtMajorStepFlag
#define rtmGetContTimeOutputInconsistentWithStateAtMajorStepFlag(rtm) ((rtm)->CTOutputIncnstWithState)
#endif

#ifndef rtmSetContTimeOutputInconsistentWithStateAtMajorStepFlag
#define rtmSetContTimeOutputInconsistentWithStateAtMajorStepFlag(rtm, val) ((rtm)->CTOutputIncnstWithState = (val))
#endif

#ifndef rtmGetDerivCacheNeedsReset
#define rtmGetDerivCacheNeedsReset(rtm) ((rtm)->derivCacheNeedsReset)
#endif

#ifndef rtmSetDerivCacheNeedsReset
#define rtmSetDerivCacheNeedsReset(rtm, val) ((rtm)->derivCacheNeedsReset = (val))
#endif

#ifndef rtmGetFinalTime
#define rtmGetFinalTime(rtm)           ((rtm)->Timing.tFinal)
#endif

#ifndef rtmGetIntgData
#define rtmGetIntgData(rtm)            ((rtm)->intgData)
#endif

#ifndef rtmSetIntgData
#define rtmSetIntgData(rtm, val)       ((rtm)->intgData = (val))
#endif

#ifndef rtmGetOdeF
#define rtmGetOdeF(rtm)                ((rtm)->odeF)
#endif

#ifndef rtmSetOdeF
#define rtmSetOdeF(rtm, val)           ((rtm)->odeF = (val))
#endif

#ifndef rtmGetOdeY
#define rtmGetOdeY(rtm)                ((rtm)->odeY)
#endif

#ifndef rtmSetOdeY
#define rtmSetOdeY(rtm, val)           ((rtm)->odeY = (val))
#endif

#ifndef rtmGetPeriodicContStateIndices
#define rtmGetPeriodicContStateIndices(rtm) ((rtm)->periodicContStateIndices)
#endif

#ifndef rtmSetPeriodicContStateIndices
#define rtmSetPeriodicContStateIndices(rtm, val) ((rtm)->periodicContStateIndices = (val))
#endif

#ifndef rtmGetPeriodicContStateRanges
#define rtmGetPeriodicContStateRanges(rtm) ((rtm)->periodicContStateRanges)
#endif

#ifndef rtmSetPeriodicContStateRanges
#define rtmSetPeriodicContStateRanges(rtm, val) ((rtm)->periodicContStateRanges = (val))
#endif

#ifndef rtmGetRTWExtModeInfo
#define rtmGetRTWExtModeInfo(rtm)      ((rtm)->extModeInfo)
#endif

#ifndef rtmGetZCCacheNeedsReset
#define rtmGetZCCacheNeedsReset(rtm)   ((rtm)->zCCacheNeedsReset)
#endif

#ifndef rtmSetZCCacheNeedsReset
#define rtmSetZCCacheNeedsReset(rtm, val) ((rtm)->zCCacheNeedsReset = (val))
#endif

#ifndef rtmGetdX
#define rtmGetdX(rtm)                  ((rtm)->derivs)
#endif

#ifndef rtmSetdX
#define rtmSetdX(rtm, val)             ((rtm)->derivs = (val))
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

#ifndef rtmGetT
#define rtmGetT(rtm)                   (rtmGetTPtr((rtm))[0])
#endif

#ifndef rtmGetTFinal
#define rtmGetTFinal(rtm)              ((rtm)->Timing.tFinal)
#endif

#ifndef rtmGetTPtr
#define rtmGetTPtr(rtm)                ((rtm)->Timing.t)
#endif

#ifndef rtmGetTStart
#define rtmGetTStart(rtm)              ((rtm)->Timing.tStart)
#endif

/* user code (top of header file) */
#include "act2_wrapper.h"

/* Block signals (default storage) */
typedef struct {
  real_T level_displaysmootheddisplayonl;
  /* '<Root>/level_display (smoothed, display only — not used for control).' */
  real_T applied_V;                    /* '<S5>/valve_guard' */
  real_T applied_V_d;                  /* '<S4>/pump_guard' */
  real_T level;                        /* '<S2>/level_calc' */
  uint16_T dist;                       /* '<S2>/tof_read' */
  uint8_T guard;                       /* '<S5>/valve_guard' */
  uint8_T guard_b;                     /* '<S4>/pump_guard' */
  uint8_T status;                      /* '<S2>/tof_read' */
  uint8_T newData;                     /* '<S2>/tof_read' */
  uint8_T status_p;                    /* '<S1>/MATLAB Function' */
  boolean_T valid;                     /* '<S2>/level_calc' */
  boolean_T newOut;                    /* '<S2>/level_calc' */
  boolean_T pump_en;                   /* '<S1>/MATLAB Function' */
  boolean_T valve_en;                  /* '<S1>/MATLAB Function' */
} B_mixr1_v2_dev_T;

/* Block states (default storage) for system '<Root>' */
typedef struct {
  real_T runSteps;                     /* '<S5>/valve_guard' */
  real_T offSteps;                     /* '<S5>/valve_guard' */
  real_T runSteps_g;                   /* '<S4>/pump_guard' */
  real_T offSteps_m;                   /* '<S4>/pump_guard' */
  real_T buf[3];                       /* '<S2>/level_calc' */
  real_T n;                            /* '<S2>/level_calc' */
  real_T age;                          /* '<S2>/level_calc' */
  real_T lvl;                          /* '<S2>/level_calc' */
  real_T prevMode;                     /* '<S1>/MATLAB Function' */
  struct {
    void *LoggedData[3];
  } Scope_PWORK;                       /* '<Root>/Scope' */

  struct {
    void *LoggedData[4];
  } Scope1_PWORK;                      /* '<Root>/Scope1' */

  struct {
    void *LoggedData[2];
  } Scope2_PWORK;                      /* '<Root>/Scope2' */

  struct {
    void *LoggedData[2];
  } Scope3_PWORK;                      /* '<Root>/Scope3' */

  boolean_T doneDoubleBufferReInit;    /* '<S5>/valve_guard' */
  boolean_T atFloor;                   /* '<S5>/valve_guard' */
  boolean_T latched;                   /* '<S5>/valve_guard' */
  boolean_T doneDoubleBufferReInit_a;  /* '<S4>/pump_guard' */
  boolean_T atCeiling;                 /* '<S4>/pump_guard' */
  boolean_T latched_e;                 /* '<S4>/pump_guard' */
  boolean_T doneDoubleBufferReInit_l;  /* '<Root>/MATLAB Function' */
  boolean_T started;                   /* '<Root>/MATLAB Function' */
  boolean_T doneDoubleBufferReInit_p;  /* '<S2>/tof_read' */
  boolean_T started_d;                 /* '<S2>/tof_read' */
  boolean_T doneDoubleBufferReInit_i;  /* '<S2>/level_calc' */
  boolean_T have;                      /* '<S2>/level_calc' */
  boolean_T doneDoubleBufferReInit_o;  /* '<S1>/MATLAB Function' */
  boolean_T sw;                        /* '<S1>/MATLAB Function' */
  boolean_T armed;                     /* '<S1>/MATLAB Function' */
} DW_mixr1_v2_dev_T;

/* Continuous states (default storage) */
typedef struct {
  real_T level_displaysmootheddisplayonl;
  /* '<Root>/level_display (smoothed, display only — not used for control).' */
} X_mixr1_v2_dev_T;

/* State derivatives (default storage) */
typedef struct {
  real_T level_displaysmootheddisplayonl;
  /* '<Root>/level_display (smoothed, display only — not used for control).' */
} XDot_mixr1_v2_dev_T;

/* State disabled  */
typedef struct {
  boolean_T level_displaysmootheddisplayonl;
  /* '<Root>/level_display (smoothed, display only — not used for control).' */
} XDis_mixr1_v2_dev_T;

#ifndef ODE3_INTG
#define ODE3_INTG

/* ODE3 Integration Data */
typedef struct {
  real_T *y;                           /* output */
  real_T *f[3];                        /* derivatives */
} ODE3_IntgData;

#endif

/* Parameters (default storage) */
struct P_mixr1_v2_dev_T_ {
  real_T mixr1_benchtof_offset_mm_Value;/* Expression: mixr1_bench.tof_offset_mm
                                         * Referenced by: '<S2>/mixr1_bench.tof_offset_mm'
                                         */
  real_T mixr1_benchtof_budget_ms_Value;/* Expression: mixr1_bench.tof_budget_ms
                                         * Referenced by: '<S2>/mixr1_bench.tof_budget_ms'
                                         */
  real_T gain_Value;                   /* Expression: mixr1_bench.tof_gain
                                        * Referenced by: '<S2>/gain'
                                        */
  real_T intercept_Value;              /* Expression: mixr1_bench.tof_intercept
                                        * Referenced by: '<S2>/intercept'
                                        */
  real_T zero_Value;                   /* Expression: mixr1_bench.zero_mm
                                        * Referenced by: '<S2>/zero'
                                        */
  real_T thickness_Value;              /* Expression: mixr1_bench.thickness_mm
                                        * Referenced by: '<S2>/thickness'
                                        */
  real_T lgain_Value;                  /* Expression: mixr1_bench.lgain
                                        * Referenced by: '<S2>/lgain'
                                        */
  real_T level_displaysmootheddisplayonl;
                          /* Computed Parameter: level_displaysmootheddisplayonl
                           * Referenced by: '<Root>/level_display (smoothed, display only — not used for control).'
                           */
  real_T level_displaysmootheddisplayo_c;
                          /* Computed Parameter: level_displaysmootheddisplayo_c
                           * Referenced by: '<Root>/level_display (smoothed, display only — not used for control).'
                           */
  real_T valveV_Value;                 /* Expression: 6
                                        * Referenced by: '<S1>/valveV'
                                        */
  real_T mixr1_benchmin_V_Value;       /* Expression: mixr1_bench.min_V
                                        * Referenced by: '<S1>/mixr1_bench.min_V'
                                        */
  real_T mixr1_benchmax_V_Value;       /* Expression: mixr1_bench.max_V
                                        * Referenced by: '<S1>/mixr1_bench.max_V'
                                        */
  real_T mixr1_benchmin_band_mm_Value; /* Expression: mixr1_bench.min_band_mm
                                        * Referenced by: '<S1>/mixr1_bench.min_band_mm'
                                        */
  real_T mixr1_benchvalve_floor_mm_Value;/* Expression: mixr1_bench.valve_floor_mm
                                          * Referenced by: '<S1>/mixr1_bench.valve_floor_mm'
                                          */
  real_T mixr1_benchmax_level_mm_Value;/* Expression: mixr1_bench.max_level_mm
                                        * Referenced by: '<S1>/mixr1_bench.max_level_mm'
                                        */
  real_T mixr1_benchceiling_margin_mm_Va;
                                    /* Expression: mixr1_bench.ceiling_margin_mm
                                     * Referenced by: '<S1>/mixr1_bench.ceiling_margin_mm'
                                     */
  real_T mixr1_benchmin_V_Value_i;     /* Expression: mixr1_bench.min_V
                                        * Referenced by: '<S4>/mixr1_bench.min_V'
                                        */
  real_T mixr1_benchmax_V_Value_c;     /* Expression: mixr1_bench.max_V
                                        * Referenced by: '<S4>/mixr1_bench.max_V'
                                        */
  real_T mixr1_benchmax_level_mmmixr1_be;
         /* Expression: mixr1_bench.max_level_mm - mixr1_bench.ceiling_margin_mm
          * Referenced by: '<S4>/mixr1_bench.max_level_mm - mixr1_bench.ceiling_margin_mm'
          */
  real_T mixr1_benchmax_run_s_Value;   /* Expression: mixr1_bench.max_run_s
                                        * Referenced by: '<S4>/mixr1_bench.max_run_s'
                                        */
  real_T mixr1_benchmin_V_Value_a;     /* Expression: mixr1_bench.min_V
                                        * Referenced by: '<S5>/mixr1_bench.min_V'
                                        */
  real_T mixr1_benchmax_V_Value_g;     /* Expression: mixr1_bench.max_V
                                        * Referenced by: '<S5>/mixr1_bench.max_V'
                                        */
  real_T mixr1_benchvalve_floor_mm_Val_p;/* Expression: mixr1_bench.valve_floor_mm
                                          * Referenced by: '<S5>/mixr1_bench.valve_floor_mm'
                                          */
  real_T mixr1_benchmax_run_s_Value_c; /* Expression: mixr1_bench.max_run_s
                                        * Referenced by: '<S5>/mixr1_bench.max_run_s'
                                        */
  real_T mixr1_benchpump_on_counts_Value;/* Expression: mixr1_bench.pump_on_counts
                                          * Referenced by: '<Root>/mixr1_bench.pump_on_counts'
                                          */
  real_T mixr1_benchvalve_on_counts_Valu;
                                      /* Expression: mixr1_bench.valve_on_counts
                                       * Referenced by: '<Root>/mixr1_bench.valve_on_counts'
                                       */
};

/* Real-time Model Data Structure */
struct tag_RTM_mixr1_v2_dev_T {
  const char_T *errorStatus;
  RTWExtModeInfo *extModeInfo;
  RTWSolverInfo solverInfo;
  X_mixr1_v2_dev_T *contStates;
  int_T *periodicContStateIndices;
  real_T *periodicContStateRanges;
  real_T *derivs;
  XDis_mixr1_v2_dev_T *contStateDisabled;
  boolean_T zCCacheNeedsReset;
  boolean_T derivCacheNeedsReset;
  boolean_T CTOutputIncnstWithState;
  real_T odeY[1];
  real_T odeF[3][1];
  ODE3_IntgData intgData;

  /*
   * Sizes:
   * The following substructure contains sizes information
   * for many of the model attributes such as inputs, outputs,
   * dwork, sample times, etc.
   */
  struct {
    uint32_T checksums[4];
    int_T numContStates;
    int_T numPeriodicContStates;
    int_T numSampTimes;
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
    time_T stepSize0;
    uint32_T clockTick1;
    time_T tStart;
    time_T tFinal;
    SimTimeStep simTimeStep;
    boolean_T stopRequestedFlag;
    time_T *t;
    time_T tArray[2];
  } Timing;
};

/* Block parameters (default storage) */
extern P_mixr1_v2_dev_T mixr1_v2_dev_P;

/* Block signals (default storage) */
extern B_mixr1_v2_dev_T mixr1_v2_dev_B;

/* Continuous states (default storage) */
extern X_mixr1_v2_dev_T mixr1_v2_dev_X;

/* Disabled states (default storage) */
extern XDis_mixr1_v2_dev_T mixr1_v2_dev_XDis;

/* Block states (default storage) */
extern DW_mixr1_v2_dev_T mixr1_v2_dev_DW;

/*
 * Exported Global Parameters
 *
 * Note: Exported global parameters are tunable parameters with an exported
 * global storage class designation.  Code generation will declare the memory for
 * these parameters and exports their symbols.
 *
 */
extern real_T student_band;            /* Variable: student_band
                                        * Referenced by: '<Root>/band'
                                        */
extern real_T student_mode;            /* Variable: student_mode
                                        * Referenced by: '<Root>/mode'
                                        */
extern real_T student_pumpV;           /* Variable: student_pumpV
                                        * Referenced by: '<Root>/pumpV'
                                        */
extern real_T student_sp;              /* Variable: student_sp
                                        * Referenced by: '<Root>/setpoint'
                                        */

/* Model entry point functions */
extern void mixr1_v2_dev_initialize(void);
extern void mixr1_v2_dev_step(void);
extern void mixr1_v2_dev_terminate(void);

/* Real-time Model object */
extern RT_MODEL_mixr1_v2_dev_T *const mixr1_v2_dev_M;
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
 * '<Root>' : 'mixr1_v2_dev'
 * '<S1>'   : 'mixr1_v2_dev/Controller'
 * '<S2>'   : 'mixr1_v2_dev/Level Sensor'
 * '<S3>'   : 'mixr1_v2_dev/MATLAB Function'
 * '<S4>'   : 'mixr1_v2_dev/Pump Guard'
 * '<S5>'   : 'mixr1_v2_dev/Valve Guard'
 * '<S6>'   : 'mixr1_v2_dev/Controller/MATLAB Function'
 * '<S7>'   : 'mixr1_v2_dev/Level Sensor/level_calc'
 * '<S8>'   : 'mixr1_v2_dev/Level Sensor/tof_read'
 * '<S9>'   : 'mixr1_v2_dev/Pump Guard/pump_guard'
 * '<S10>'  : 'mixr1_v2_dev/Valve Guard/valve_guard'
 */
#endif                                 /* mixr1_v2_dev_h_ */

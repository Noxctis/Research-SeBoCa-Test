/* tof_wrapper.h */
#ifndef TOF_WRAPPER_H
#define TOF_WRAPPER_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
int  tof_init(int16_t offset_mm, uint16_t timing_budget_ms);
void tof_step(uint16_t *distance_mm, uint8_t *range_status, uint8_t *new_data);
void tof_stop(void);
#ifdef __cplusplus
}
#endif
#endif
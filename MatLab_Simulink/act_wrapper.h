#ifndef ACT_WRAPPER_H
#define ACT_WRAPPER_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
int  act_init(void);
void act_step(uint8_t pump_on, uint16_t pump_pwm);
void act_stop(void);
#ifdef __cplusplus
}
#endif
#endif
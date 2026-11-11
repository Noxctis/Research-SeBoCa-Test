#ifndef ACT2_WRAPPER_H
#define ACT2_WRAPPER_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
int  act2_init(void);                              /* safe to call more than once; parks both outputs */
void act2_pump(uint8_t on, uint16_t counts);       /* independent of the valve */
void act2_valve(uint8_t on, uint16_t counts);      /* independent of the pump */
void act2_stop(void);                              /* both outputs off; call when the model stops */
#ifdef __cplusplus
}
#endif
#endif

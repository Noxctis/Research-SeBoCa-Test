/* act_wrapper.c - pump only, same pins as setPump() in mixr1_fluid_controller.cpp */
#include <stdint.h>
#include <wiringPi.h>
#include "act_wrapper.h"

#define PUMP_EN      15
#define PUMP_INA     17
#define PUMP_INB     27
#define PUMP_PWM     13   /* hardware PWM1 */
#define PWM_RANGE  1024

static int ready = 0;

static void park(void)
{
    digitalWrite(PUMP_EN, LOW);
    digitalWrite(PUMP_INA, LOW);
    digitalWrite(PUMP_INB, LOW);
    pwmWrite(PUMP_PWM, 0);
}

int act_init(void)
{
    if (wiringPiSetupGpio() == -1) return 1;
    pinMode(PUMP_EN, OUTPUT);
    pinMode(PUMP_INA, OUTPUT);
    pinMode(PUMP_INB, OUTPUT);
    pinMode(PUMP_PWM, PWM_OUTPUT);
    park();
    ready = 1;
    return 0;
}

void act_step(uint8_t pump_on, uint16_t pump_pwm)
{
    if (!ready) return;
    if (pump_pwm > PWM_RANGE) pump_pwm = PWM_RANGE;
    if (pump_on) {
        digitalWrite(PUMP_EN, HIGH);
        digitalWrite(PUMP_INA, HIGH);
        digitalWrite(PUMP_INB, LOW);
        pwmWrite(PUMP_PWM, pump_pwm);
    } else {
        park();
    }
}

void act_stop(void)
{
    if (ready) park();
    ready = 0;
}
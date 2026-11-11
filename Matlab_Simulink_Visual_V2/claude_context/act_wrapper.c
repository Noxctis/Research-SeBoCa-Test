/* act_wrapper.c - pump + solenoid, same pins and calls as setPump()/setSolenoid() */
#include <stdint.h>
#include <wiringPi.h>
#include "act_wrapper.h"

#define PUMP_EN    15
#define PUMP_INA   17
#define PUMP_INB   27
#define PUMP_PWM   13   /* hardware PWM1 */
#define SOL_INA     5
#define SOL_INB     6
#define SOL_PWM    12   /* hardware PWM0 */
#define PWM_RANGE 1024
/* HARD CAP 50 %: the supply is 24 V and the pump and the solenoid valve are both rated 12 V, so the average voltage at
   the load may never go above 24 V x 50 % = 12 V, whatever the model asks for (pumpV / valveV above 12 are clipped here). */
#define PWM_MAX   (PWM_RANGE / 2)

static int ready = 0;

static void park(void)
{
    digitalWrite(PUMP_EN, LOW);
    digitalWrite(PUMP_INA, LOW);
    digitalWrite(PUMP_INB, LOW);
    pwmWrite(PUMP_PWM, 0);
    digitalWrite(SOL_INA, LOW);
    digitalWrite(SOL_INB, LOW);
    pwmWrite(SOL_PWM, 0);
}

int act_init(void)
{
    if (wiringPiSetupGpio() == -1) return 1;
    pinMode(PUMP_EN, OUTPUT);  pinMode(PUMP_INA, OUTPUT); pinMode(PUMP_INB, OUTPUT);
    pinMode(PUMP_PWM, PWM_OUTPUT);
    pinMode(SOL_INA, OUTPUT);  pinMode(SOL_INB, OUTPUT);
    pinMode(SOL_PWM, PWM_OUTPUT);
    park();
    ready = 1;
    return 0;
}

void act_step(uint8_t pump_on, uint16_t pump_pwm, uint8_t valve_on, uint16_t valve_pwm)
{
    if (!ready) return;
       /* never both at once */
    if (pump_pwm  > PWM_MAX) pump_pwm  = PWM_MAX;     /* 50 % = 12 V average */
    if (valve_pwm > PWM_MAX) valve_pwm = PWM_MAX;

    if (pump_on) {
        digitalWrite(PUMP_EN, HIGH);
        digitalWrite(PUMP_INA, HIGH);
        digitalWrite(PUMP_INB, LOW);
        pwmWrite(PUMP_PWM, pump_pwm);
    } else {
        digitalWrite(PUMP_EN, LOW);
        digitalWrite(PUMP_INA, LOW);
        digitalWrite(PUMP_INB, LOW);
        pwmWrite(PUMP_PWM, 0);
    }

    if (valve_on) {
        digitalWrite(SOL_INA, HIGH);
        digitalWrite(SOL_INB, LOW);
        pwmWrite(SOL_PWM, valve_pwm);
    } else {
        digitalWrite(SOL_INA, LOW);
        digitalWrite(SOL_INB, LOW);
        pwmWrite(SOL_PWM, 0);
    }
}

void act_stop(void)
{
    if (ready) park();
    ready = 0;
}
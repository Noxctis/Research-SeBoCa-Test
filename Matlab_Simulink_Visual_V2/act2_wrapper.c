/* act2_wrapper.c - v2 pump and valve outputs as two independent calls.
   Same pins, same drive sequence and same wiringPi setup as v1 act_wrapper.c, so the electrical
   behaviour matches what has already been run on this bench. */
#include <stdint.h>
#include <stdlib.h>
#include <signal.h>
#include <wiringPi.h>
#include "act2_wrapper.h"

#define PUMP_EN    15
#define PUMP_INA   17
#define PUMP_INB   27
#define PUMP_PWM   13   /* hardware PWM1 */
#define SOL_EN     14   /* M2 enable on the dual VNH5019 - added when the valve channel's own enable line was wired in */
#define SOL_INA     5
#define SOL_INB     6
#define SOL_PWM    12   /* hardware PWM0 */

/* HARD COUNT LIMITS (out of 1024). These are the only values v1 has run on this bench:
   pump 149 counts (3.5 V requested) and valve 192 counts (4.5 V requested), which read about
   6 V and 12 V at the driver with a multimeter. The counts-to-volts relation has NOT been measured
   with an oscilloscope, so nothing above these may be driven.
   Raise them only after measuring the driver output. They apply whatever the model asks for. */
#define PUMP_COUNTS_MAX   149
#define VALVE_COUNTS_MAX  192

static int ready = 0;

static void pump_off(void)
{
    digitalWrite(PUMP_EN, LOW);
    digitalWrite(PUMP_INA, LOW);
    digitalWrite(PUMP_INB, LOW);
    pwmWrite(PUMP_PWM, 0);
}

static void valve_off(void)
{
    digitalWrite(SOL_EN, LOW);
    digitalWrite(SOL_INA, LOW);
    digitalWrite(SOL_INB, LOW);
    pwmWrite(SOL_PWM, 0);
}

/* The hardware PWM keeps running after a program ends, so both outputs must be turned off on the way out:
   on a normal exit (atexit), and on a stop request or crash (signal handlers). SIGKILL cannot be caught. */
static void on_signal(int sig)
{
    act2_stop();
    signal(sig, SIG_DFL);
    raise(sig);
}

static void install_exit_handlers(void)
{
    static int done = 0;
    if (done) return;
    done = 1;
    atexit(act2_stop);
    signal(SIGINT,  on_signal);
    signal(SIGTERM, on_signal);
    signal(SIGHUP,  on_signal);
    signal(SIGQUIT, on_signal);
    signal(SIGABRT, on_signal);
    signal(SIGSEGV, on_signal);
    signal(SIGBUS,  on_signal);
    signal(SIGFPE,  on_signal);
}

int act2_init(void)
{
    if (ready) return 0;
    if (wiringPiSetupGpio() == -1) return 1;     /* on failure nothing is ever driven */
    pinMode(PUMP_EN, OUTPUT);  pinMode(PUMP_INA, OUTPUT); pinMode(PUMP_INB, OUTPUT);
    pinMode(PUMP_PWM, PWM_OUTPUT);
    pinMode(SOL_EN, OUTPUT);
    pinMode(SOL_INA, OUTPUT);  pinMode(SOL_INB, OUTPUT);
    pinMode(SOL_PWM, PWM_OUTPUT);
    pump_off();
    valve_off();
    install_exit_handlers();
    ready = 1;
    return 0;
}

void act2_pump(uint8_t on, uint16_t counts)
{
    if (!ready) return;
    if (!on || counts == 0) { pump_off(); return; }
    if (counts > PUMP_COUNTS_MAX) counts = PUMP_COUNTS_MAX;
    digitalWrite(PUMP_EN, HIGH);
    digitalWrite(PUMP_INA, HIGH);
    digitalWrite(PUMP_INB, LOW);
    pwmWrite(PUMP_PWM, counts);
}

void act2_valve(uint8_t on, uint16_t counts)
{
    if (!ready) return;
    if (!on || counts == 0) { valve_off(); return; }
    if (counts > VALVE_COUNTS_MAX) counts = VALVE_COUNTS_MAX;
    digitalWrite(SOL_EN, HIGH);
    digitalWrite(SOL_INA, HIGH);
    digitalWrite(SOL_INB, LOW);
    pwmWrite(SOL_PWM, counts);
}

void act2_stop(void)
{
    if (ready) { pump_off(); valve_off(); }
    ready = 0;
}
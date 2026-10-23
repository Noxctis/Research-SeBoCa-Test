#include "tof_wrapper.h"
#ifndef TOF_SIM
#include "VL53L4CD_api.h"
#include "platform.h"
#define DEV 0x52
#endif

static int      running = 0;
static uint16_t last_dist = 0;
static uint8_t  last_status = 255;

int tof_init(int16_t offset_mm, uint16_t budget_ms)
{
#ifdef TOF_SIM
    (void)offset_mm; (void)budget_ms;
    running = 1;
    return 0;
#else
    uint16_t id = 0;
    if (VL53L4CD_PlatformInit() != 0)                        return 1;
    if (VL53L4CD_GetSensorId(DEV, &id) != 0 || id != 0xEBAA) return 2;
    if (VL53L4CD_SensorInit(DEV) != 0)                       return 3;
    if (VL53L4CD_SetRangeTiming(DEV, budget_ms, 0) != 0)     return 4;
    if (VL53L4CD_SetOffset(DEV, offset_mm) != 0)             return 5;
    VL53L4CD_StartTemperatureUpdate(DEV);
    if (VL53L4CD_StartRanging(DEV) != 0)                     return 6;
    running = 1;
    return 0;
#endif
}

void tof_step(uint16_t *dist, uint8_t *status, uint8_t *new_data)
{
    *new_data = 0;
#ifdef TOF_SIM
    static uint16_t n = 0;
    last_dist = (uint16_t)(150 - (n++ % 100));   /* fake falling distance */
    last_status = 0;
    *new_data = 1;
#else
    uint8_t ready = 0;
    if (running && VL53L4CD_CheckForDataReady(DEV, &ready) == 0 && ready) {
        VL53L4CD_ResultsData_t r;
        if (VL53L4CD_GetResult(DEV, &r) == 0) {
            last_dist = r.distance_mm;
            last_status = r.range_status;
            *new_data = 1;
        }
        VL53L4CD_ClearInterrupt(DEV);
    }
#endif
    *dist = last_dist;
    *status = last_status;
}

void tof_stop(void)
{
#ifndef TOF_SIM
    if (running) VL53L4CD_StopRanging(DEV);
#endif
    running = 0;
}
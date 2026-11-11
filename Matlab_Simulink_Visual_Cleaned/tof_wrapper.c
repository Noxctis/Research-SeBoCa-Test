/* tof_wrapper.c - real sensor only, with auto-recovery when frames stop */
#include <stdint.h>
#include "VL53L4CD_api.h"
#include "platform.h"

#define DEV 0x52
#define SILENT_LIMIT 30                 /* steps without a frame before restart (1.5 s at 50 ms) */
static int      running = 0;
static uint16_t last_dist = 0;
static uint8_t  last_status = 255;      /* 255 = no data yet */
static int16_t  g_off = 0;
static uint16_t g_bud = 200;
static int      silent = 0;

static int sensor_start(void)
{
    if (VL53L4CD_SensorInit(DEV) != 0)                   return 3;
    if (VL53L4CD_SetRangeTiming(DEV, g_bud, 0) != 0)     return 4;
    if (VL53L4CD_SetOffset(DEV, g_off) != 0)             return 5;
    VL53L4CD_StartTemperatureUpdate(DEV);
    if (VL53L4CD_StartRanging(DEV) != 0)                 return 6;
    return 0;
}

int tof_init(int16_t offset_mm, uint16_t budget_ms)
{
    uint16_t id = 0;
    g_off = offset_mm;  g_bud = budget_ms;  silent = 0;

    if (VL53L4CD_PlatformInit() != 0)                         return 1;
    if (VL53L4CD_GetSensorId(DEV, &id) != 0 || id != 0xEBAA)  return 2;
    {
        int r = sensor_start();
        if (r != 0) return r;
    }
    running = 1;
    return 0;
}

void tof_step(uint16_t *dist, uint8_t *status, uint8_t *new_data)
{
    uint8_t ready = 0;
    *new_data = 0;
    if (running && VL53L4CD_CheckForDataReady(DEV, &ready) == 0 && ready) {
        VL53L4CD_ResultsData_t r;
        if (VL53L4CD_GetResult(DEV, &r) == 0) {
            last_dist = r.distance_mm;
            last_status = r.range_status;
            *new_data = 1;
        }
        VL53L4CD_ClearInterrupt(DEV);
    }
    if (running) {
        if (*new_data) {
            silent = 0;
        } else if (++silent > SILENT_LIMIT) {
            VL53L4CD_StopRanging(DEV);
            sensor_start();             /* if this fails, we try again in 1.5 s */
            silent = 0;
        }
    }
    *dist = last_dist;
    *status = last_status;
}

void tof_stop(void)
{
    if (running) VL53L4CD_StopRanging(DEV);
    running = 0;
}
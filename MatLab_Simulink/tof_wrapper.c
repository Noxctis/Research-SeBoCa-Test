/* tof_wrapper.c - real sensor only (the PC simulation uses the block's own fake code) */
#include <stdint.h>
#include "VL53L4CD_api.h"
#include "platform.h"

#define DEV 0x52
static int      running = 0;
static uint16_t last_dist = 0;
static uint8_t  last_status = 255;      /* 255 = no data yet */

int tof_init(int16_t offset_mm, uint16_t budget_ms)
{
    uint16_t id = 0;
    
    if (VL53L4CD_PlatformInit() != 0)                         return 1;
    if (VL53L4CD_GetSensorId(DEV, &id) != 0 || id != 0xEBAA)  return 2;
    if (VL53L4CD_SensorInit(DEV) != 0)                        return 3;
    if (VL53L4CD_SetRangeTiming(DEV, budget_ms, 0) != 0)      return 4;
    if (VL53L4CD_SetOffset(DEV, offset_mm) != 0)              return 5;
    VL53L4CD_StartTemperatureUpdate(DEV);
    if (VL53L4CD_StartRanging(DEV) != 0)                      return 6;
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
    *dist = last_dist;
    *status = last_status;
}

void tof_stop(void)
{
    if (running) VL53L4CD_StopRanging(DEV);
    running = 0;
}
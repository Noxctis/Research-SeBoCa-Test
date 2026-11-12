function actuators(pump_V, valve_V, pump_counts, valve_counts) %#codegen
% Drives the pump and valve through act2_wrapper.c. Pi build only; PC simulation does nothing here.
% pump_V and valve_V are the guards' applied_V (read from the hidden tags MIXR1_PUMP_V and
% MIXR1_VALVE_V, so nothing but a guard can switch a device). 0 means off, anything above 0 means on.
% pump_counts and valve_counts come from the bench file and are the maximum drive for each device.
% Pump: pump_V (multimeter volts) is mapped to counts by a measured table, so pumpV now changes the PWM. Valve: fixed at valve_counts
% (on/off only). The counts-to-volts relation at the driver is still unmeasured with a scope.
coder.extrinsic('which', 'fileparts');
persistent started
if isempty(started), started = false; end
if ~coder.target('Sfun')
    srcDir = coder.const(fileparts(which('act2_wrapper.c')));
    coder.cinclude('act2_wrapper.h');
    coder.updateBuildInfo('addIncludePaths', srcDir);
    coder.updateBuildInfo('addSourcePaths',  srcDir);
    coder.updateBuildInfo('addSourceFiles', 'act2_wrapper.c');
    coder.updateBuildInfo('addLinkFlags', '-lwiringPi');
    if ~started
        coder.ceval('act2_init');
        started = true;
    end
    % Pump: pump_V is the target in volts as read by a multimeter at the pump terminals. Bench calibration
    % (24 V supply, counts = 149*s/12 for s = 1..12) measured: below. Counts are interpolated from it
    % and never exceed pump_counts, so a target above the last point (10.9 V) just gives full drive.
    % The last point (167 counts, 12.0 V) is extrapolated from the trend, NOT measured: check it with the meter.
    CAL_V = [0 1.92 3.2 4.1 4.9 5.7 6.5 7.2 7.9 8.7 9.4 10.2 10.9 12.0];
    CAL_C = [0 12 25 37 50 62 75 87 99 112 124 137 149 167];
    t  = double(pump_V);
    pc = CAL_C(end);
    if t < CAL_V(end)
        for k = 2:numel(CAL_V)
            if t <= CAL_V(k)
                pc = CAL_C(k-1) + (CAL_C(k) - CAL_C(k-1)) * (t - CAL_V(k-1)) / (CAL_V(k) - CAL_V(k-1));
                break
            end
        end
    end
    pc = min(pc, double(pump_counts));
    if pump_V > 0, pc = max(pc, 1); end
    coder.ceval('act2_pump',  uint8(pump_V  > 0), uint16(round(pc)));
    coder.ceval('act2_valve', uint8(valve_V > 0), uint16(valve_counts));
end
end

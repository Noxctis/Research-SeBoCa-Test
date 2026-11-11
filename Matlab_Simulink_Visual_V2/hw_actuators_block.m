function actuators(pump_V, valve_V, pump_counts, valve_counts) %#codegen
% Drives the pump and valve through act2_wrapper.c. Pi build only; PC simulation does nothing here.
% pump_V and valve_V are the guards' applied_V (read from the hidden tags MIXR1_PUMP_V and
% MIXR1_VALVE_V, so nothing but a guard can switch a device). 0 means off, anything above 0 means on.
% pump_counts and valve_counts come from the bench file. The volts value is NOT converted to PWM counts:
% its relation to the driver output has not been measured, so each device runs at one fixed, proven drive level.
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
    coder.ceval('act2_pump',  uint8(pump_V  > 0), uint16(pump_counts));
    coder.ceval('act2_valve', uint8(valve_V > 0), uint16(valve_counts));
end
end

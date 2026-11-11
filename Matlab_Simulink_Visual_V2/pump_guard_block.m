function [applied_V, guard] = pump_guard(cmd, enable, level, valid, min_V, max_V, trip, max_run_s) %#codegen
% Pump safety guard (locked block). Forces the pump off whatever the Controller or a student asks.
% cmd, enable : from the Controller or a Dashboard switch (volts at the load, on/off)
% level, valid: from the Level Sensor
% min_V, max_V, trip, max_run_s: bench file (Constant blocks inside this block)
%   trip = max_level_mm - ceiling_margin_mm
% guard: 0 ok | 1 no valid level | 3 level at the ceiling | 4 continuous-run limit
DT = 0.05;  RELEASE = 5;  REST_S = 2;
persistent atCeiling runSteps offSteps latched
if isempty(atCeiling)
    atCeiling = false; runSteps = 0; offSteps = 0; latched = false;
end

want  = enable && cmd > 0;                       % NaN or negative commands mean off
sees  = valid && isfinite(level);

if sees
    if level >= trip
        atCeiling = true;
    elseif level <= trip - RELEASE               % resumes only 5 mm below the trip level
        atCeiling = false;
    end
end

if want                                          % run limit is cleared after REST_S seconds commanded off
    offSteps = 0;
else
    offSteps = min(offSteps + 1, 1e6);
    if offSteps * DT >= REST_S
        runSteps = 0;
        latched  = false;
    end
end

if ~sees
    guard = uint8(1);
elseif atCeiling
    guard = uint8(3);
elseif latched
    guard = uint8(4);
else
    guard = uint8(0);
end

if want && guard == 0
    runSteps = runSteps + 1;
    if runSteps * DT >= max_run_s
        latched = true;
        guard   = uint8(4);
    end
end

applied_V = 0;
if want && guard == 0
    applied_V = min(max(cmd, min_V), max_V);
end
end

function [applied_V, guard] = valve_guard(cmd, enable, level, valid, min_V, max_V, floor_mm, max_run_s) %#codegen
% Valve safety guard (locked block). Forces the valve closed whatever the Controller or a student asks.
% cmd, enable : from the Controller or a Dashboard switch (volts at the load, on/off)
% level, valid: from the Level Sensor
% min_V, max_V, floor_mm, max_run_s: bench file (Constant blocks inside this block)
% guard: 0 ok | 1 no valid level | 4 continuous-open limit | 5 level at the floor (valve held closed)
DT = 0.05;  RELEASE = 2;  REST_S = 2;
persistent atFloor runSteps offSteps latched
if isempty(atFloor)
    atFloor = false; runSteps = 0; offSteps = 0; latched = false;
end

want = enable && cmd > 0;                        % NaN or negative commands mean closed
sees = valid && isfinite(level);

if sees
    if level <= floor_mm
        atFloor = true;
    elseif level >= floor_mm + RELEASE           % reopens only 2 mm above the floor
        atFloor = false;
    end
end

if want                                          % run limit is cleared after REST_S seconds commanded closed
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
elseif atFloor
    guard = uint8(5);
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

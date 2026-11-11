function [pump_V, pump_en, valve_V, valve_en, status, sp_used, band_used] = controller( ...
        mode, setpoint, band_pct, pumpV, valveV, level, valid, ...
        min_V, max_V, min_band, floor_mm, max_level, margin) %#codegen
% MIXR1 Controller (locked block). Students set only: mode, setpoint, band_pct (and pumpV where it is exposed).
% band_pct: half-width of the switching window as a percentage of the setpoint in use (students use 5 to 10).
% valveV is not a student knob: the valve is on or off, so valveV is fixed at 6 V (the Constant stays at 6).
% mode 0: off
% mode 1: pump always on at pumpV, the valve switches (opens above setpoint+band, closes below setpoint-band)
% mode 2: valve always open at valveV, the pump switches (on below setpoint-band, off above setpoint+band)
% mode 3: instructor drain. Valve open, pump off. The Valve Guard closes the valve at the 2 mm floor. Not a student mode.
% The last six inputs come from the bench file (Constant blocks inside this block), not from students.
% status: 0 off | 1 raising | 2 lowering | 3 no valid level | 4 waiting for mode 0 after start
% Startup lockout: on the Pi nothing runs until mode has been 0 at least once since the program started,
% so a model that starts with mode 1 or 2 left on cannot switch the pump or valve by itself.
% In Simulink PC simulation (the Sfun target) the lockout is skipped.
persistent sw prevMode armed
if isempty(sw), sw = false; prevMode = 0; armed = coder.target('Sfun'); end   % sw = the switching device is on

trip      = max_level - margin;                              % the Pump guard cuts at this level
p         = min(max(band_pct, 0), 50) / 100;                 % percent -> fraction
sp1       = min(setpoint, trip / (1 + p));                   % top of the window never above the trip level
band_used = min(max(sp1 * p, min_band), (trip - floor_mm) / 2);
sp_used   = min(max(sp1, floor_mm + band_used), trip - band_used);
pump_V    = min(max(pumpV,  min_V), max_V);                  % volts at the load, min_V..max_V
valve_V   = min(max(valveV, min_V), max_V);

if mode ~= prevMode, sw = false; end                         % changing mode restarts the switching
prevMode = mode;

if mode == 0, armed = true; end
wanted  = (mode == 1 || mode == 2 || mode == 3);
active  = armed && wanted;
pump_en = false;
valve_en = false;
status  = uint8(0);

if ~active || ~valid
    sw = false;
    if active
        status = uint8(3);                                   % wanted to run, but no valid level
    elseif wanted
        status = uint8(4);                                   % mode is on but the controller is not armed yet
    end
elseif mode == 3
    sw       = false;
    pump_en  = false;
    valve_en = true;
    status   = uint8(2);                                     % lowering
elseif mode == 1
    if level >= sp_used + band_used
        sw = true;
    elseif level <= sp_used - band_used
        sw = false;
    end
    pump_en  = true;
    valve_en = sw;
    status   = uint8(1 + double(sw));                        % valve open: lowering
else
    if level <= sp_used - band_used
        sw = true;
    elseif level >= sp_used + band_used
        sw = false;
    end
    pump_en  = sw;
    valve_en = true;
    status   = uint8(2 - double(sw));                        % pump on: raising
end
end

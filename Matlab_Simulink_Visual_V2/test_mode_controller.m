function test_mode_controller
% Logic test for mode_controller_block.m with a FAKE tank:
%   level' = KF*pump_V*pump_en - KD*valve_V*valve_en        (KF, KD are placeholders, not your tank)
% band is a percentage of the setpoint (5 at a setpoint of 100 mm is 5 mm).
% Checks the switching logic and the limits only. No hardware, no Simulink.
% Run from the folder that contains mode_controller_block.m.
KF = 0.25;  KD = 0.30;  DT = 0.05;
L = struct('min_V',6,'max_V',12,'min_band',2,'floor',2,'max_level',250,'margin',10);

% 1. off, and no valid level
clear functions
[~, pe, ~, ve, s] = run1(0, 100, 5, 6, 6, 50, true, L);
chk(~pe && ~ve && s == 0, 'mode 0: both off, status 0');
[~, pe, ~, ve, s] = run1(1, 100, 5, 6, 6, 50, false, L);
chk(~pe && ~ve && s == 3, 'no valid level: both off, status 3');

% 1b. startup lockout: mode 1 or 2 from the very start does nothing until mode 0 has been seen
clear functions
[~, pe, ~, ve, s] = controller_block_call(1, 100, 5, 6, 6, 50, true, L);
chk(~pe && ~ve && s == 4, 'mode 1 at start: pump and valve stay off, status 4 (waiting for mode 0)');
[~, pe, ~, ve, s] = controller_block_call(2, 100, 5, 6, 6, 50, true, L);
chk(~pe && ~ve && s == 4, 'mode 2 at start: still off while never armed');
controller_block_call(0, 100, 5, 6, 6, 50, true, L);
[~, pe, ~, ve, s] = controller_block_call(2, 100, 5, 6, 6, 50, true, L);
chk(pe && ve && s == 1, 'after one step in mode 0, mode 2 runs');
[~, pe, ~, ve, s] = controller_block_call(0, 100, 5, 6, 6, 50, true, L);
chk(~pe && ~ve && s == 0, 'back to mode 0: everything off');

% 1c. instructor drain (mode 3): valve open, pump never on
clear functions
arm(L);
for lv = [250 100 5]
    [~, pe, ~, ve, s] = controller_block_call(3, 100, 5, 6, 6, lv, true, L);
    chk(~pe && ve && s == 2, sprintf('mode 3 at %d mm: valve open, pump off, status 2', lv));
end
[~, pe, ~, ve, s] = controller_block_call(3, 100, 5, 6, 6, 50, false, L);
chk(~pe && ~ve && s == 3, 'mode 3 with no valid level: both off, status 3');
clear functions
[~, pe, ~, ve, s] = controller_block_call(3, 100, 5, 6, 6, 100, true, L);
chk(~pe && ~ve && s == 4, 'mode 3 at start: still locked out until mode 0 has been seen');

% 2. voltage limits
clear functions
[p, ~, v] = run1(1, 100, 5, 3, 20, 50, true, L);
chk(p == 6 && v == 12, 'volts clamped to 6..12');

% 3. setpoint and band limits (band is a percentage of the setpoint; trip = 240 here)
clear functions
[~, ~, ~, ~, ~, sp, b] = run1(1, 400, 5, 6, 6, 50, true, L);
chk(abs(sp + b - 240) < 1e-9 && abs(b - 0.05 * sp) < 1e-9, 'setpoint kept so the top of the window is at the trip level, band still 5% of it');
[~, ~, ~, ~, ~, sp, b] = run1(1, 250, 10, 6, 6, 50, true, L);
chk(abs(sp + b - 240) < 1e-9 && abs(b - 0.10 * sp) < 1e-9, '250 mm at 10%: setpoint lowered so the window top is the trip level');
[~, ~, ~, ~, ~, sp, b] = run1(1, 200, 10, 6, 6, 50, true, L);
chk(sp == 200 && abs(b - 20) < 1e-9, '200 mm at 10%: band is 20 mm, nothing limited');
[~, ~, ~, ~, ~, sp, b] = run1(1, 50, 5, 6, 6, 50, true, L);
chk(sp == 50 && abs(b - 2.5) < 1e-9, '50 mm at 5%: band is 2.5 mm');
[~, ~, ~, ~, ~, sp, b] = run1(1, 0, 5, 6, 6, 50, true, L);
chk(sp == 4 && b == 2, 'setpoint kept so the bottom of the window is above the floor');
[~, ~, ~, ~, ~, sp, b] = run1(1, 100, 0, 6, 6, 50, true, L);
chk(b == 2 && sp == 100, 'band raised to the minimum when the percentage is too small');

% 4. mode 1: pump always on, valve switches, level stays in the window
[lvl, pe, ve, tog] = sim_loop(1, 100, 5, 6, 12, 60, KF, KD, DT, L);
chk(all(pe), 'mode 1: pump on the whole time');
chk(min(lvl(end-1000:end)) >= 94 && max(lvl(end-1000:end)) <= 106, ...
    sprintf('mode 1: level stays in %.1f..%.1f mm (window 95..105)', min(lvl(end-1000:end)), max(lvl(end-1000:end))));
chk(tog >= 4 && tog <= 60, sprintf('mode 1: valve switched %d times (no chatter)', tog));

% 5. mode 2: valve always on, pump switches
[lvl, pe, ve, tog] = sim_loop(2, 100, 5, 12, 6, 60, KF, KD, DT, L);
chk(all(ve), 'mode 2: valve open the whole time');
chk(min(lvl(end-1000:end)) >= 94 && max(lvl(end-1000:end)) <= 106, ...
    sprintf('mode 2: level stays in %.1f..%.1f mm (window 95..105)', min(lvl(end-1000:end)), max(lvl(end-1000:end))));
chk(tog >= 4 && tog <= 60, sprintf('mode 2: pump switched %d times (no chatter)', tog));

% 6. a wrong pairing (pump too weak in mode 2) must NOT be hidden: level falls, pump stays on
[lvl, pe] = sim_loop(2, 100, 5, 6, 12, 60, KF, KD, DT, L);
chk(lvl(end) < 20 && pe(end), 'mode 2 with a weak pump: level sinks, pump stays on (the guard floor handles the rest)');

% 7. changing mode restarts the switching
clear functions
arm(L);
controller_block_call(1, 100, 5, 6, 6, 200, true, L);              % mode 1, level high -> valve opens
[~, pe, ~, ve] = controller_block_call(2, 100, 5, 6, 6, 100, true, L);   % mode 2, level in window
chk(~pe && ve, 'after a mode change the pump starts off, valve open');

disp('All mode controller logic tests passed.');
end

function varargout = run1(mode, sp, band, pV, vV, lvl, valid, L)
arm(L);
[varargout{1:7}] = controller_block_call(mode, sp, band, pV, vV, lvl, valid, L);
end

function varargout = controller_block_call(mode, sp, band, pV, vV, lvl, valid, L)
[varargout{1:7}] = mode_controller_block(mode, sp, band, pV, vV, lvl, valid, ...
    L.min_V, L.max_V, L.min_band, L.floor, L.max_level, L.margin);
end

function [lvl, pe, ve, tog] = sim_loop(mode, sp, band, pV, vV, lvl0, KF, KD, DT, L)
clear functions
arm(L);
n = 6000;  lvl = zeros(1, n);  pe = false(1, n);  ve = false(1, n);
x = lvl0;
for k = 1:n
    [p, pen, v, ven] = controller_block_call(mode, sp, band, pV, vV, x, true, L);
    x = max(0, x + DT * (KF * p * pen - KD * v * ven));
    lvl(k) = x;  pe(k) = pen;  ve(k) = ven;
end
if mode == 1, sw = ve; else, sw = pe; end
tog = sum(diff(sw) ~= 0);
end

function arm(L)
% the controller only runs after it has seen mode 0 once (as on the Pi)
mode_controller_block(0, 100, 5, 6, 6, 50, true, L.min_V, L.max_V, L.min_band, L.floor, L.max_level, L.margin);
end

function chk(ok, msg)
if ok, fprintf('  ok    %s\n', msg); else, error('FAILED: %s', msg); end
end

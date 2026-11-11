function test_guards
% Logic test for pump_guard_block.m and valve_guard_block.m.
% Part 1 drives each guard directly, including bypass attempts. Part 2 runs the mode Controller
% plus both guards on a FAKE tank (level' = KF*pumpV - KD*valveV, placeholders, not your tank).
% No hardware, no Simulink. Run from the folder that contains the *_block.m files.
MINV = 6;  MAXV = 12;  TRIP = 240;  FLOOR = 2;  DT = 0.05;

% ---------------- pump guard ----------------
clear functions
[v, g] = pump_guard_block(3, true, 100, true, MINV, MAXV, TRIP, 1800);
chk(v == 6 && g == 0, 'pump: 3 V request is raised to 6 V');
[v, ~] = pump_guard_block(1000, true, 100, true, MINV, MAXV, TRIP, 1800);
chk(v == 12, 'pump: huge request is clamped to 12 V');
[v, ~] = pump_guard_block(-5, true, 100, true, MINV, MAXV, TRIP, 1800);
chk(v == 0, 'pump: negative request gives 0');
[v, ~] = pump_guard_block(NaN, true, 100, true, MINV, MAXV, TRIP, 1800);
chk(v == 0, 'pump: NaN request gives 0');
[v, g] = pump_guard_block(8, false, 100, true, MINV, MAXV, TRIP, 1800);
chk(v == 0 && g == 0, 'pump: enable false gives 0');
[v, g] = pump_guard_block(8, true, 100, false, MINV, MAXV, TRIP, 1800);
chk(v == 0 && g == 1, 'pump: no valid level -> off, guard 1');
[v, g] = pump_guard_block(8, true, NaN, true, MINV, MAXV, TRIP, 1800);
chk(v == 0 && g == 1, 'pump: NaN level treated as no valid level');

clear functions
[v, g] = pump_guard_block(8, true, 241, true, MINV, MAXV, TRIP, 1800);
chk(v == 0 && g == 3, 'pump: level above trip -> off, guard 3');
[v, g] = pump_guard_block(8, true, 237, true, MINV, MAXV, TRIP, 1800);
chk(v == 0 && g == 3, 'pump: stays off at 237 (hysteresis)');
[v, g] = pump_guard_block(8, true, 235, true, MINV, MAXV, TRIP, 1800);
chk(v == 8 && g == 0, 'pump: resumes at 235');

clear functions
for k = 1:199, [v, g] = pump_guard_block(8, true, 100, true, MINV, MAXV, TRIP, 10); end
chk(v == 8 && g == 0, 'pump: still running just under the run limit (10 s)');
[v, g] = pump_guard_block(8, true, 100, true, MINV, MAXV, TRIP, 10);
chk(v == 0 && g == 4, 'pump: continuous-run limit trips, guard 4');
for k = 1:200, [v, g] = pump_guard_block(8, true, 100, true, MINV, MAXV, TRIP, 10); end
chk(v == 0 && g == 4, 'pump: stays latched while still commanded on');
for k = 1:41, pump_guard_block(8, false, 100, true, MINV, MAXV, TRIP, 10); end
[v, g] = pump_guard_block(8, true, 100, true, MINV, MAXV, TRIP, 10);
chk(v == 8 && g == 0, 'pump: run limit clears after 2 s commanded off');

% ---------------- valve guard ----------------
clear functions
[v, g] = valve_guard_block(3, true, 100, true, MINV, MAXV, FLOOR, 1800);
chk(v == 6 && g == 0, 'valve: 3 V request is raised to 6 V');
[v, ~] = valve_guard_block(99, true, 100, true, MINV, MAXV, FLOOR, 1800);
chk(v == 12, 'valve: huge request is clamped to 12 V');
[v, g] = valve_guard_block(8, true, 100, false, MINV, MAXV, FLOOR, 1800);
chk(v == 0 && g == 1, 'valve: no valid level -> closed, guard 1');
clear functions
[v, g] = valve_guard_block(8, true, 1.5, true, MINV, MAXV, FLOOR, 1800);
chk(v == 0 && g == 5, 'valve: level at the floor -> closed, guard 5');
[v, g] = valve_guard_block(8, true, 3, true, MINV, MAXV, FLOOR, 1800);
chk(v == 0 && g == 5, 'valve: stays closed at 3 mm (hysteresis)');
[v, g] = valve_guard_block(8, true, 4.5, true, MINV, MAXV, FLOOR, 1800);
chk(v == 8 && g == 0, 'valve: reopens at 4.5 mm');
clear functions
for k = 1:198, valve_guard_block(8, true, 100, true, MINV, MAXV, FLOOR, 10); end
[v, g] = valve_guard_block(8, true, 100, true, MINV, MAXV, FLOOR, 10);   % the 199th call
chk(v == 8 && g == 0, 'valve: still open just under the run limit (10 s)');
[v, g] = valve_guard_block(8, true, 100, true, MINV, MAXV, FLOOR, 10);
chk(v == 0 && g == 4, 'valve: continuous-open limit trips, guard 4');

% ---------------- Controller + guards on a fake tank ----------------
KF = 0.25;  KD = 0.30;
% (a) pump out-fills the valve in mode 1: the Controller cannot hold the level, the guard must
[lvl, gp] = closed_loop(1, 100, 5, 12, 6, 60, KF, KD, DT, MINV, MAXV, TRIP, FLOOR);
chk(max(lvl) <= TRIP + 0.5, sprintf('mode 1, pump too strong: level never above %.1f mm (trip %d)', max(lvl), TRIP));
chk(any(gp == 3), 'mode 1, pump too strong: ceiling guard (3) did act');
% (b) pump too weak in mode 2: the level sinks, the floor guard must stop the drain
[lvl, ~, gv] = closed_loop(2, 100, 5, 6, 12, 60, KF, KD, DT, MINV, MAXV, TRIP, FLOOR);
chk(min(lvl) >= FLOOR - 0.5, sprintf('mode 2, pump too weak: level never below %.1f mm (floor %d)', min(lvl), FLOOR));
chk(any(gv == 5), 'mode 2, pump too weak: floor guard (5) did act');
% (c) a correct pairing is not disturbed by the guards
[lvl, gp, gv] = closed_loop(1, 100, 5, 6, 12, 60, KF, KD, DT, MINV, MAXV, TRIP, FLOOR);
chk(all(gp(1:end) == 0) && all(gv(1:end) == 0), 'mode 1, correct pairing: guards stay quiet');
chk(min(lvl(end-1000:end)) >= 94 && max(lvl(end-1000:end)) <= 106, 'mode 1, correct pairing: level held in the window');

% (d) instructor drain from a high level: the valve empties the tank to the floor and the pump never runs
[lvl, gp, gv, pumpRan] = drain_loop(KF, KD, DT, MINV, MAXV, TRIP, FLOOR);
chk(~pumpRan, 'drain mode: the pump never runs');
chk(min(lvl) >= FLOOR - 0.5 && lvl(end) < 5, sprintf('drain mode: level falls to %.1f mm and stops at the floor', lvl(end)));
chk(any(gv == 5), 'drain mode: floor guard (5) closes the valve');

disp('All guard tests passed.');
end

function [lvl, gp, gv] = closed_loop(mode, sp, band, pV, vV, lvl0, KF, KD, DT, MINV, MAXV, TRIP, FLOOR)
clear functions
mode_controller_block(0, 100, 5, 6, 6, 50, true, MINV, MAXV, 2, FLOOR, 250, 10);   % arm, as on the Pi
n = 6000;  lvl = zeros(1, n);  gp = zeros(1, n);  gv = zeros(1, n);
x = lvl0;
for k = 1:n
    [pv, pe, vv, ve] = mode_controller_block(mode, sp, band, pV, vV, x, true, MINV, MAXV, 2, FLOOR, 250, 10);
    [pa, g1] = pump_guard_block(pv, pe, x, true, MINV, MAXV, TRIP, 1800);
    [va, g2] = valve_guard_block(vv, ve, x, true, MINV, MAXV, FLOOR, 1800);
    x = max(0, x + DT * (KF * pa - KD * va));
    lvl(k) = x;  gp(k) = g1;  gv(k) = g2;
end
end

function [lvl, gp, gv, pumpRan] = drain_loop(KF, KD, DT, MINV, MAXV, TRIP, FLOOR)
clear functions
mode_controller_block(0, 100, 5, 6, 6, 50, true, MINV, MAXV, 2, FLOOR, 250, 10);   % arm
n = 8000;  lvl = zeros(1, n);  gp = zeros(1, n);  gv = zeros(1, n);  pumpRan = false;
x = 150;
for k = 1:n
    [pv, pe, vv, ve] = mode_controller_block(3, 100, 5, 6, 6, x, true, MINV, MAXV, 2, FLOOR, 250, 10);
    [pa, g1] = pump_guard_block(pv, pe, x, true, MINV, MAXV, TRIP, 1800);
    [va, g2] = valve_guard_block(vv, ve, x, true, MINV, MAXV, FLOOR, 1800);
    pumpRan = pumpRan || pa > 0;
    x = max(0, x + DT * (KF * pa - KD * va));
    lvl(k) = x;  gp(k) = g1;  gv(k) = g2;
end
end

function chk(ok, msg)
if ok, fprintf('  ok    %s\n', msg); else, error('FAILED: %s', msg); end
end

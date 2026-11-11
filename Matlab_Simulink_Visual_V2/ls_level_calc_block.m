function [level, valid, newOut, raw, corr] = level_calc(dist, status, newData, gain, intercept, zero, thickness, lgain) %#codegen
% Replaces tof_correct and the level maths that used to sit inside fluid_ctrl.
%   corr  = (raw - intercept) / gain          same formula as tof_correct
%   level = max(0, lgain * (zero - median3(corr) - thickness))   same as fluid_ctrl v1
% valid is true only if a good frame (status 0, corr in 30..2000 mm) arrived within the
% last MAX_AGE steps. Bad or missing frames never refresh it, so valid drops after 0.6 s.
% 12 steps = 3 frame periods at the longest allowed budget (200 ms), so 2 lost frames are tolerated.
MAX_AGE = 12;

persistent buf n age have lvl rawV corrV
if isempty(buf)
    buf = zeros(1,3); n = 0; age = 1e6; have = false;
    lvl = 0; rawV = 0; corrV = 0;
end

newOut = (newData == 1);
if newData == 1
    d = (double(dist) - intercept) / gain;
    if status == 0 && d > 30 && d <= 2000
        buf  = [buf(2:3), d];
        n    = min(n + 1, 3);
        age  = 0;
        have = true;
        rawV = double(dist);
        corrV = d;
        lvl  = max(0, lgain * (zero - median(buf(4-n:3)) - thickness));
    else
        age = min(age + 1, 1e6);
    end
else
    age = min(age + 1, 1e6);
end

level = lvl;
valid = have && (age <= MAX_AGE);
raw   = rawV;
corr  = corrV;
end

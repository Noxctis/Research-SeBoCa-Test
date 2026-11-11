function b = load_bench(file)
% b = load_bench('bench_mixr1.json')
% Reads the per-bench calibration, checks it, and puts it in the base workspace as
% mixr1_bench (a plain struct, so Simulink inlines it: not tunable in external mode).
% Changing the file means: run load_bench again, then rebuild and redeploy the model.
if nargin < 1
    file = fullfile(fileparts(mfilename('fullpath')), 'bench_mixr1.json');
end
if ~isfile(file), error('load_bench:nofile', 'Bench file not found: %s', file); end
b = jsondecode(fileread(file));

req = {'bench','host','tof_offset_mm','tof_budget_ms','tof_gain','tof_intercept', ...
       'zero_mm','thickness_mm','lgain','max_level_mm','ceiling_margin_mm', ...
       'valve_floor_mm','min_V','max_V','min_band_mm','max_run_s', ...
       'pump_on_counts','valve_on_counts'};
miss = req(~isfield(b, req));
if ~isempty(miss)
    error('load_bench:missing', 'Missing field(s): %s', strjoin(miss, ', '));
end
for i = 3:numel(req)
    v = b.(req{i});
    if ~isnumeric(v) || ~isscalar(v) || ~isfinite(v)
        error('load_bench:bad', '%s must be a finite number.', req{i});
    end
end

if b.tof_offset_mm < -32768 || b.tof_offset_mm > 32767 || b.tof_offset_mm ~= round(b.tof_offset_mm)
    error('load_bench:bad', 'tof_offset_mm must be a whole number that fits int16.');
end
if b.tof_budget_ms < 10 || b.tof_budget_ms > 200
    error('load_bench:bad', 'tof_budget_ms must be 10..200 (the 0.6 s stale limit assumes this).');
end
if b.tof_gain <= 0 || b.lgain <= 0
    error('load_bench:bad', 'tof_gain and lgain must be > 0.');
end
if b.zero_mm <= 30
    error('load_bench:bad', 'zero_mm must be > 30.');
end
if b.max_level_mm <= 0 || b.max_level_mm >= b.zero_mm - 30
    error('load_bench:bad', 'max_level_mm must be between 0 and zero_mm - 30.');
end
if b.ceiling_margin_mm < 0 || b.ceiling_margin_mm >= b.max_level_mm
    error('load_bench:bad', 'ceiling_margin_mm must be >= 0 and < max_level_mm.');
end

for f = {'pump_on_counts','valve_on_counts'}
    c = b.(f{1});
    if c < 1 || c > 512 || c ~= round(c)
        error('load_bench:bad', '%s must be a whole number from 1 to 512 (act2_wrapper.c clamps it further).', f{1});
    end
end
if b.max_run_s <= 0
    error('load_bench:bad', 'max_run_s must be > 0.');
end
if b.valve_floor_mm < 0
    error('load_bench:bad', 'valve_floor_mm must be >= 0.');
end
if b.min_V <= 0 || b.max_V < b.min_V || b.max_V > 12
    error('load_bench:bad', 'Need 0 < min_V <= max_V <= 12 (12 V is the hard cap in act_wrapper.c).');
end
if b.min_band_mm < 0 || (b.max_level_mm - b.ceiling_margin_mm - b.valve_floor_mm) < 2 * b.min_band_mm
    error('load_bench:bad', 'min_band_mm is too large for the space between the floor and the trip level.');
end

assignin('base', 'mixr1_bench', b);
fprintf(['Bench %s: offset %d mm, gain %.5f, intercept %.3f, zero %g mm, thickness %g mm, ' ...
         'lgain %g, spill level %g mm (guard margin %g mm), valve floor %g mm, ' ...
         'volts %g..%g, min band %g mm, run limit %g s, drive counts pump %d valve %d\n'], ...
    b.bench, b.tof_offset_mm, b.tof_gain, b.tof_intercept, b.zero_mm, b.thickness_mm, ...
    b.lgain, b.max_level_mm, b.ceiling_margin_mm, b.valve_floor_mm, b.min_V, b.max_V, b.min_band_mm, b.max_run_s, b.pump_on_counts, b.valve_on_counts);
end
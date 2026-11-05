function T = process_feedback(target, ruler)
% target: final target in mm for this run; ruler: ruler readings, one per cycle, in order
if nargin < 2, ruler = []; end
logdata = evalin('base','logdata');
save(sprintf('logfb_%03d_%s.mat', target, char(datetime('now','Format','HHmmss'))), 'logdata');

d  = squeeze(logdata.Data); if size(d,2) ~= 6, d = d.'; end
t  = logdata.Time(:);
lv = d(:,4);  st = d(:,5);
prev   = [0; st(1:end-1)];
starts = find(st == 5 & prev ~= 5);
n = numel(starts);
if n == 0, error('No feedback cycles (state 5) found in logdata.'); end
ruler = ruler(:); ruler(end+1:n) = NaN; ruler = ruler(1:n);

rows = nan(n, 8);
for i = 1:n
    a = starts(i);
    e = find(st(a:end) == 3 | st(a:end) == 9, 1) + a - 1;   % end of this cycle
    if isempty(e), e = numel(st); end
    seg  = a:e;
    peak = max(lv(seg));                                      % highest level reached

    i6 = seg(st(seg) == 6);                                   % level after the first settle
    if isempty(i6)
        settled1 = NaN;
    else
        brk = find(diff(i6) > 1, 1);
        if isempty(brk), brk = numel(i6); end
        settled1 = lv(i6(brk));
    end

    inTrim = ismember(st(seg), [7 8]);
    trims  = sum(inTrim(2:end) & ~inTrim(1:end-1));           % number of trim corrections

    final = NaN; fstd = NaN; nf = 0;
    if st(e) == 3
        p = e;
        while p < numel(st) && st(p+1) == 3, p = p + 1; end
        pl   = e:p;                                           % the state 3 plateau
        good = pl(d(pl,3) == 1 & d(pl,2) == 0);
        good = good(max(1, end-4):end);                       % last 5 good frames
        final = mean(lv(good)); fstd = std(lv(good)); nf = numel(good);
    end
    rows(i,:) = [i, peak, settled1, trims, final, fstd, t(e) - t(a), nf];
end

T = array2table(rows, 'VariableNames', ...
    {'Cycle','Peak_mm','Settled1_mm','Trims','Final_mm','Final_std_mm','Duration_s','N_frames'});
T.Target_mm = repmat(target, n, 1);
T.Ruler_mm  = ruler;
T.Error_mm  = T.Final_mm - T.Ruler_mm;
disp(T)
f = 'feedback_measurements.csv';
writetable(T, f, 'WriteMode','append', 'WriteVariableNames', ~isfile(f));
end
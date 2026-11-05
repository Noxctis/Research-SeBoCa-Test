function T = process_level(level, ruler)
% level : target in mm for this run (50, 100, ...)
% ruler : your ruler readings in mm, one per fill, in order (NaN if unknown)
if nargin < 2, ruler = []; end
logdata = evalin('base','logdata');
save(sprintf('logdata_%03d_%s.mat', level, char(datetime('now','Format','HHmmss'))), 'logdata');

d = squeeze(logdata.Data); if size(d,2) ~= 6, d = d.'; end
isDone   = d(:,5) == 3;
startIdx = find(diff([0; isDone]) == 1);
endIdx   = find(diff([isDone; 0]) == -1);
n = numel(startIdx);
if n == 0, error('No finished fills (state 3) found.'); end
if ~isempty(ruler) && numel(ruler) ~= n
    warning('%d fills found but %d ruler values given.', n, numel(ruler));
end
ruler = ruler(:); ruler(end+1:n) = NaN; ruler = ruler(1:n);

rows = nan(n, 6);
for i = 1:n
    seg  = startIdx(i):endIdx(i);
    good = seg(d(seg,3) == 1 & d(seg,2) == 0);   % new frame, status 0
    good = good(max(1, end-4):end);              % last 5 good readings
    rows(i,:) = [level, i, mean(d(good,4)), std(d(good,4)), mean(d(good,1)), numel(good)];
end
T = array2table(rows, 'VariableNames', ...
    {'Target_mm','Rep','ToF_level_mm','ToF_std_mm','ToF_dist_mm','N_frames'});
T.Ruler_mm = ruler;
T.Error_mm = T.ToF_level_mm - T.Ruler_mm;
disp(T)
f = 'all_measurements.csv';
writetable(T, f, 'WriteMode','append', 'WriteVariableNames', ~isfile(f));
end

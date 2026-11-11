d = squeeze(logdata.Data);
if size(d,2) ~= 6, d = d.'; end
t = logdata.Time(:);
dist = d(:,1); status = d(:,2); newData = d(:,3); level = d(:,4); mark = d(:,6);

rows = [];
for m = unique(mark(mark > 0))'
    idx = find(mark == m & newData == 1 & status == 0);
    idx = idx(1:min(5, numel(idx)));
    for k = 1:numel(idx)
        rows = [rows; m, k, t(idx(k)), dist(idx(k)), level(idx(k))]; %#ok<AGROW>
    end
end
T = array2table(rows, 'VariableNames', {'Mark_mm','Sample','Time_s','ToF_dist_mm','ToF_level_mm'});
disp(T)
writetable(T, 'level_points.csv');
disp(groupsummary(T, 'Mark_mm', {'mean','std'}, 'ToF_level_mm'))
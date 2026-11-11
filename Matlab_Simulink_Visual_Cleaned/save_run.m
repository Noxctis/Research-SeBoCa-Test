function dirn = save_run(tag)
% save_run            saves logdata + vizlog into runs/<timestamp>/
% save_run('test1')   same, with a label in the folder name
if nargin < 1, tag = ''; else, tag = ['_' tag]; end
root = fullfile(fileparts(which('init_params')), 'runs');
if ~isfolder(root), mkdir(root); end
dirn = fullfile(root, [char(datetime('now','Format','yyyyMMdd_HHmmss')) tag]);
mkdir(dirn);

logdata = evalin('base','logdata');
vizlog  = evalin('base','vizlog');
d = squeeze(logdata.Data); if size(d,2) ~= 6, d = d.'; end
t = logdata.Time(:);
v = squeeze(vizlog.Data);  if size(v,2) ~= 6, v = v.'; end
v = interp1(vizlog.Time(:), v, t, 'nearest', 'extrap');   % align to logdata time

T = array2table([t d v(:,2:6)], 'VariableNames', {'time_s','dist_mm','status', ...
    'newData','level_mm','state','mark','target_mm','tol_lo_mm','tol_hi_mm', ...
    'hyst_low_mm','hyst_high_mm'});
writetable(T, fullfile(dirn,'run.csv'));
save(fullfile(dirn,'run.mat'), 'logdata', 'vizlog');

fig = figure('Visible','off','Position',[100 100 900 600]);
subplot(2,1,1); plot(t,T.level_mm,'b',t,T.target_mm,'k--',t,T.tol_lo_mm,'g:', ...
    t,T.tol_hi_mm,'g:',t,T.hyst_low_mm,'r--',t,T.hyst_high_mm,'r--');
ylabel('mm'); grid on; legend('level','target','tol lo','tol hi','hyst low','hyst high');
subplot(2,1,2); stairs(t,T.state); ylabel('state'); xlabel('s'); grid on;
exportgraphics(fig, fullfile(dirn,'scope.png')); close(fig);
fprintf('Saved run to %s\n', dirn);
end
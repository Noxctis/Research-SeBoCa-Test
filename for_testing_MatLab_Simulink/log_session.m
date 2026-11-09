function [logDir, session] = log_session(label)
% [logDir, session] = log_session          current session (auto-created if none)
% log_session('calib2')                    start a new session called calib2_<time>
logDir = fullfile(fileparts(mfilename('fullpath')), 'logs');
if ~isfolder(logDir), mkdir(logDir); end
if nargin >= 1
    stamp = char(datetime('now','Format','yyyyMMdd_HHmmss'));
    s = sprintf('%s_%s', char(label), stamp);
    assignin('base', 'fc_session', s);
end
if evalin('base', 'exist(''fc_session'',''var'')')
    session = evalin('base', 'fc_session');
else
    session = char(datetime('now','Format','yyyyMMdd_HHmmss'));
    assignin('base', 'fc_session', session);
end
end
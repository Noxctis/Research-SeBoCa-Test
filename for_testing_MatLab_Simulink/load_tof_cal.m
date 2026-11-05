function load_tof_cal(offsetFile, fitFile)
off = sscanf(fileread(offsetFile), '%f', 1);
f   = sscanf(fileread(fitFile), '%f %f', 2);          % [gain; intercept]
mk = @(name, v) assignin('base', name, setStorage(Simulink.Parameter(v)));
mk('fc_tofOffset',    int16(off));
mk('fc_tofGain',      f(1));
mk('fc_tofIntercept', f(2));
fprintf('Loaded offset %d mm, gain %.5f, intercept %.3f\n', off, f(1), f(2));
end
function p = setStorage(p)
p.CoderInfo.StorageClass = 'ExportedGlobal';
end

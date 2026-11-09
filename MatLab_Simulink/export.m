modelName = 'mixr1_level';          % <-- the exact name from dir *.slx
if ~isfile([modelName '.slx']), error('Model %s.slx not found in %s', modelName, pwd); end
out = 'claude_context'; if ~isfolder(out), mkdir(out); end
load_system(modelName);
ch = sfroot().find('-isa','Stateflow.EMChart');
for k = 1:numel(ch)
    fid = fopen(fullfile(out,[matlab.lang.makeValidName(ch(k).Name) '_block.m']),'w');
    fwrite(fid, ch(k).Script); fclose(fid);
end
disp({ch.Name}')                         % check the block names look right
files = {'ctl_wrapper.c','ctl_wrapper.h','act_wrapper.c','act_wrapper.h', ...
         'tof_wrapper.c','tof_wrapper.h','platform.c','platform.h', ...
         'init_params.m','fc.m','fc_preset.m','process_level.m','process_feedback.m', ...
         'fit_tof_sweep.m','load_tof_cal.m','all_measurements.csv', ...
         'feedback_measurements.csv','tof_sweep_points.csv','STARTUP_FROM_SHUTDOWN.txt'};
for k = 1:numel(files)
    if isfile(files{k}), copyfile(files{k}, out); else, fprintf('missing: %s\n', files{k}); end
end
b = find_system(modelName,'LookUnderMasks','all','BlockType','Constant');
for k = 1:numel(b), fprintf('%s = %s\n', b{k}, get_param(b{k},'Value')); end
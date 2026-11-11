function mixr1_setup(benchFile)
% mixr1_setup            run once per MATLAB session, or from the model's PreLoadFcn callback
% mixr1_setup(file)      use a different bench file
% Loads the bench calibration and limits, and creates the three student values as tunable
% parameters so Dashboard blocks can change them while the model runs on the Pi.
% The mode always starts at 0 (everything off).
here = fileparts(mfilename('fullpath'));
addpath(here);
if nargin < 1
    benchFile = fullfile(here, 'bench_mixr1.json');
end
load_bench(benchFile);

mk('student_mode', 0);      % 0 off, 1 or 2 = student modes (3 = instructor drain, set from MATLAB only)
mk('student_sp',   100);    % setpoint in mm (students use 50 to 250)
mk('student_band', 5);      % band in percent of the setpoint (students use 5 to 10)
fprintf('Student values ready: mode 0, setpoint 100 mm, band 5 %%.\n');
end

function mk(name, value)
p = Simulink.Parameter(value);
p.CoderInfo.StorageClass = 'ExportedGlobal';
assignin('base', name, p);
end

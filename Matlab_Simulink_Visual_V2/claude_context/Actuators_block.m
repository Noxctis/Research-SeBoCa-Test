function actuators(pumpOn, pumpPwm, valveOn, valvePwm) %#codegen
coder.extrinsic('which', 'fileparts');
persistent started
if isempty(started), started = false; end
if ~coder.target('Sfun')
    srcDir = coder.const(fileparts(which('act_wrapper.c')));
    coder.cinclude('act_wrapper.h');
    coder.updateBuildInfo('addIncludePaths', srcDir);
    coder.updateBuildInfo('addSourcePaths',  srcDir);
    coder.updateBuildInfo('addSourceFiles', 'act_wrapper.c');
    coder.updateBuildInfo('addLinkFlags', '-lwiringPi');
    if ~started
        coder.ceval('act_init');
        started = true;
    end
    coder.ceval('act_step', pumpOn, pumpPwm, valveOn, valvePwm);
end
end
function [dist, status, newData] = tof_read() %#codegen
coder.extrinsic('which', 'fileparts');
dist    = uint16(0);
status  = uint8(255);
newData = uint8(0);

persistent k started
if isempty(k)
    k = uint16(0);
    started = false;
end

if coder.target('Sfun')
    dist    = uint16(150) - mod(k, uint16(100));
    k       = k + uint16(1);
    status  = uint8(0);
    newData = uint8(1);
else
    srcDir = coder.const(fileparts(which('tof_wrapper.c')));
    coder.cinclude('tof_wrapper.h');
    coder.updateBuildInfo('addIncludePaths', srcDir);
    coder.updateBuildInfo('addSourcePaths',  srcDir);
    coder.updateBuildInfo('addSourceFiles', 'tof_wrapper.c');
    coder.updateBuildInfo('addSourceFiles', 'VL53L4CD_api.c');
    coder.updateBuildInfo('addSourceFiles', 'platform.c');

    if ~started
        coder.ceval('tof_init', int16(-26), uint16(200));
        started = true;
    end
    coder.ceval('tof_step', coder.wref(dist), coder.wref(status), coder.wref(newData));
end
end
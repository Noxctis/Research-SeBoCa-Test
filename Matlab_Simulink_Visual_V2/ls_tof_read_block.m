function [dist, status, newData] = tof_read(offset_mm, budget_ms) %#codegen
% Level Sensor driver. Real VL53L4CD on the Pi, simulated frames in PC simulation.
% offset_mm and budget_ms come from the bench file through Constant blocks.
coder.extrinsic('which', 'fileparts');
dist    = uint16(0);
status  = uint8(255);
newData = uint8(0);

persistent k frame lastDist started
if isempty(k)
    k = uint32(0);
    frame = uint32(0);
    lastDist = uint16(0);
    started = false;
end

if coder.target('Sfun')
    % PC simulation only: a frame every 4th step (5 Hz). Raw distance sweeps 398..202 mm
    % (level about 8..202 mm with the default bench). Steps 400..519 are a dropout,
    % so the stale-data logic can be seen working.
    k = k + uint32(1);
    stall = (k >= uint32(400)) && (k < uint32(520));
    if mod(k, uint32(4)) == 0 && ~stall
        frame = frame + uint32(1);
        lastDist = uint16(400) - uint16(2) * uint16(mod(frame, uint32(100)));
        newData = uint8(1);
    end
    dist = lastDist;
    if frame > 0
        status = uint8(0);
    end
else
    srcDir = coder.const(fileparts(which('tof_wrapper.c')));
    coder.cinclude('tof_wrapper.h');
    coder.updateBuildInfo('addIncludePaths', srcDir);
    coder.updateBuildInfo('addSourcePaths',  srcDir);
    coder.updateBuildInfo('addSourceFiles', 'tof_wrapper.c');
    coder.updateBuildInfo('addSourceFiles', 'VL53L4CD_api.c');
    coder.updateBuildInfo('addSourceFiles', 'platform.c');

    if ~started
        coder.ceval('tof_init', int16(offset_mm), uint16(budget_ms));
        started = true;
    end
    coder.ceval('tof_step', coder.wref(dist), coder.wref(status), coder.wref(newData));
end
end

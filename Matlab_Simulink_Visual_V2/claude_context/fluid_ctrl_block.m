function [pumpOn, pumpPwm, level, state, valveOn, valvePwm, reason, viz] = fluid_ctrl( ...
        dist, status, newData, p) %#codegen
% p = [cmd target pumpV valveV drainTo overshoot tol settle zero thickness]
% cmd:   0 idle, 1 fill, 2 drain, 3 feedback fill, 4 go to target by settling,
%        5 manual drain, 6 manual pump, 7 hysteresis (valve always open, pump between low and target)
%        Any new command goes to state 0 first, then starts.
% state: 0 idle, 1 filling, 2 draining, 3 in band (keeps regulating while hold = 1),
%        4 drain done, 5 overfill, 6 settling, 7 trim-drain, 8 trim-fill, 9 fault,
%        11 manual drain, 12 manual pump, 13 hysteresis drain-down, 14 hysteresis refill
% reason (when state is 9): 1 no sensor frames, 2 invalid readings, 3 phase timeout
% live values: react, hold, low (hysteresis pump-on level, 0 = target - 10)
coder.extrinsic('which', 'fileparts');
DT         = 0.05;    % model step size in seconds (Solver: fixed-step 0.05)
GAP_STEPS  = 2;       % steps in state 0 between a new command and its start
N_MED      = 3;       % level filter length: 1 = fastest response, 3 = smoother
MAX_AGE    = 12;      % outputs stay off if the last sensor frame is older than 12 steps
EMPTY_MM   = 2.0;     % automatic drain never goes below this
MAX_BAD    = 10;      % consecutive invalid frames while pumping/draining -> fault
MAX_SILENT = 40;      % steps with no new frame while pumping/draining -> fault (2 s)
MAX_RUN    = 4800;    % max steps for one pump or valve phase (240 s)
BIG_MM     = 10;      % errors larger than this are corrected at full power
BACKOFF    = 0.5;     % each failed correction in a row uses 70% of the previous power
SCALE_MIN  = 0.2;     % never go below 20% of the commanded power
V_MAX      = 24.0;    % supply voltage: pumpV and valveV are the average volts at the load
PWM_RANGE  = 1024;

persistent st prevSt prevCmd prevSeq buf nvalid bad silent runSteps outSteps fails curScale ...
           lvl haveLvl why pending gap ctlStarted
if isempty(st)
    st = uint8(0); prevSt = uint8(0); prevCmd = uint8(0); prevSeq = 0;
    buf = zeros(1,3); nvalid = 0; bad = 0; silent = 0; runSteps = 0; outSteps = 0;
    fails = 0; curScale = 1; lvl = 0; haveLvl = false;
    why = uint8(0); pending = uint8(0); gap = 0; ctlStarted = false;
end

% ---- live control values (UDP overrides the Constant blocks) ----
defs = [reshape(double(p),1,[]), 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0];

vals = defs;
if ~coder.target('Sfun')
    srcDir = coder.const(fileparts(which('ctl_wrapper.c')));
    coder.cinclude('ctl_wrapper.h');
    coder.updateBuildInfo('addIncludePaths', srcDir);
    coder.updateBuildInfo('addSourcePaths',  srcDir);
    coder.updateBuildInfo('addSourceFiles', 'ctl_wrapper.c');
    if ~ctlStarted
        coder.ceval('ctl_init');
        ctlStarted = true;
    end
    coder.ceval('ctl_poll', coder.rref(defs), coder.wref(vals));
end
c   = uint8(min(max(round(vals(1)), 0), 255));
tgt = vals(2);  pV = vals(3);  vV = vals(4);  dTo = vals(5);
ovs = vals(6);  tl = vals(7);  stl = vals(8);  z0 = vals(9);  th = vals(10);
lg  = vals(11);                     % level scale
ld  = max(vals(12), 0);             % lead: stop this many mm early to cancel coasting
ts  = min(max(vals(13), 0), 1);     % trim power scale
rc  = max(vals(14), 0.2);           % react: seconds out of band before state 3 corrects
hd  = vals(15) >= 0.5;              % hold: 1 = state 3 keeps regulating
lowRaw = vals(16);                  % hysteresis: pump switches on at or below this level
sq  = vals(17);                     % number of command messages received
settleSteps = round(stl / DT);
reactSteps  = round(rc / DT);
if lowRaw <= 0
    lowEff = tgt - 10;
else
    lowEff = lowRaw;
end
lowEff = min(lowEff, tgt - max(tl, 2));     % keep a gap of at least the tolerance

% ---- new sensor frame ----
if newData == 1
    silent = 0;
    if status == 0 && dist > 30 && dist <= 2000
        buf = [buf(2:3), double(dist)];
        nvalid = min(nvalid + 1, 3);
        bad = 0;
        nuse = min(nvalid, N_MED);
        lvl = max(0, lg * (z0 - median(buf(4-nuse:3)) - th));
        haveLvl = true;
    else
        bad = bad + 1;
    end
else
    silent = min(silent + 1, 1e6);
end

% ---- commands: any new command goes to state 0 first, then starts ----
newCmd = (c ~= prevCmd) || (sq ~= prevSeq);
if c == 0
    st = uint8(0);
    why = uint8(0); pending = uint8(0); gap = 0;
elseif newCmd && c <= 7
    st = uint8(0);                              % everything off (also clears a fault)
    why = uint8(0);
    pending = c; gap = GAP_STEPS;
    bad = 0; runSteps = 0; outSteps = 0; fails = 0; curScale = 1;
elseif pending ~= 0
    gap = gap - 1;
    if gap <= 0
        if pending == 3
            st = uint8(5);
        elseif pending == 4
            st = uint8(6);
        elseif pending == 5
            st = uint8(11);
        elseif pending == 6
            st = uint8(12);
        elseif pending == 7
            st = uint8(13);
        else
            st = pending;                       % 1 fill, 2 drain
        end
        pending = uint8(0);
    end
end
prevCmd = c;
prevSeq = sq;

% ---- count steps spent in the current phase ----
if st ~= prevSt
    runSteps = 0;
end
prevSt = st;
ok = haveLvl && silent <= MAX_AGE;

% ---- automatic modes ----
pumping  = (st == 1 || st == 5 || st == 8 || st == 14);
draining = (st == 2 || st == 7 || st == 13 || st == 14);
if pumping || draining
    runSteps = runSteps + 1;
    limit = MAX_RUN;
    if st == 13, limit = 4 * MAX_RUN; end       % a slow drain-down may take longer
    if bad >= MAX_BAD
        st = uint8(9); why = uint8(2);
    elseif silent >= MAX_SILENT
        st = uint8(9); why = uint8(1);
    elseif runSteps >= limit
        st = uint8(9); why = uint8(3);
    elseif haveLvl
        if st == 1
            if lvl >= tgt - ld, st = uint8(3); outSteps = 0; end
        elseif st == 2
            if lvl <= max(dTo, EMPTY_MM), st = uint8(4); end
        elseif st == 5
            if lvl >= tgt + max(ovs, 0) - ld, st = uint8(6); end
        elseif st == 7
            if lvl <= tgt + ld, st = uint8(6); end
        elseif st == 8
            if lvl >= tgt - ld, st = uint8(6); end
        elseif st == 13
            if lvl <= lowEff, st = uint8(14); end       % low level reached: pump on
        elseif st == 14
            if lvl >= tgt - ld, st = uint8(13); end     % target reached: pump off, drain continues
        end
    end
elseif st == 6
    runSteps = runSteps + 1;
    if ok && runSteps >= settleSteps
        err = lvl - tgt;
        if abs(err) <= tl
            st = uint8(3); fails = 0; outSteps = 0;
        else
            fails = fails + 1;
            if abs(err) > BIG_MM
                curScale = 1;
            else
                curScale = max(SCALE_MIN, ts * BACKOFF^(fails - 1));
            end
            if err > 0
                st = uint8(7);
            else
                st = uint8(8);
            end
        end
    end
elseif st == 3 && hd
    % continuous regulation: react when the level has been outside the band for react seconds
    if ok && abs(lvl - tgt) > tl
        outSteps = outSteps + 1;
    else
        outSteps = max(0, outSteps - 2);        % in-band readings drain the counter, not reset it
    end
    if outSteps >= reactSteps
        outSteps = 0; fails = 1;
        err = lvl - tgt;
        if abs(err) > BIG_MM
            curScale = 1;
        else
            curScale = max(SCALE_MIN, ts);
        end
        if err > 0
            st = uint8(7);
        else
            st = uint8(8);
        end
    end
end

% ---- manual modes (run without a level reading) ----
if st == 11 || st == 12
    runSteps = runSteps + 1;
    if runSteps >= MAX_RUN
        st = uint8(9); why = uint8(3);
    elseif st == 12 && haveLvl && lvl >= tgt + max(ovs, 0)
        st = uint8(4);              % ceiling reached, pump stops
    end
end

% ---- outputs ----
ok      = haveLvl && silent <= MAX_AGE;
pumpOn  = uint8(((st == 1 || st == 5 || st == 8 || st == 14) && ok) || st == 12);
valveOn = uint8(((st == 2 || st == 7 || st == 13 || st == 14) && ok) || st == 11);
scale = 1.0;
if st == 7 || st == 8, scale = curScale; end
pumpPwm  = uint16(min(PWM_RANGE, max(0, round(scale * pV / V_MAX * PWM_RANGE))));
valvePwm = uint16(min(PWM_RANGE, max(0, round(scale * vV / V_MAX * PWM_RANGE))));
if c == 7, vLo = lowEff; vHi = tgt - ld; else, vLo = NaN; vHi = NaN; end
viz = [lvl, tgt, tgt - tl, tgt + tl, vLo, vHi];
level    = lvl;
state    = st;
reason   = why;
end
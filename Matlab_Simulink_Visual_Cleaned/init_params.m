% [cmd target pumpV valveV drainTo overshoot tol settle zero thickness]
fc_defaults = Simulink.Parameter([0 50 3.5 4.5 0 0 2 5 389 1]);
fc_defaults.CoderInfo.StorageClass = 'ExportedGlobal';
fc_tofOffset    = Simulink.Parameter(int16(-26)); fc_tofOffset.CoderInfo.StorageClass    = 'ExportedGlobal';
fc_tofGain      = Simulink.Parameter(1.00901);    fc_tofGain.CoderInfo.StorageClass      = 'ExportedGlobal';
fc_tofIntercept = Simulink.Parameter(14.477);     fc_tofIntercept.CoderInfo.StorageClass = 'ExportedGlobal';
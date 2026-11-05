function fc_preset
% Run after Monitor & Tune has started. Edit these numbers when you recalibrate.
fc('zero',389,'thickness',0,'lgain',1.0, ...
   'pumpV',6,'valveV',12,'overshoot',20,'tol',2,'settle',5,'drainTo',0,'lead',0,'trimScale',1);
end
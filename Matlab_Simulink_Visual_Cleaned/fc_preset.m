function fc_preset
% Run after Monitor & Tune has started. Edit these numbers when you recalibrate.
fc('zero',389,'thickness',1,'lgain',1.0, ...
   'pumpV',3.5,'valveV',4.5,'overshoot',0,'tol',2,'settle',5,'drainTo',0,'lead',4,'trimScale',0.7,'react',1,'hold',0,'low',80);
end
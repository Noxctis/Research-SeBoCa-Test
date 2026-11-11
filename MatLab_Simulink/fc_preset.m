function fc_preset
% Run after Monitor & Tune has started. Edit these numbers when you recalibrate.
fc('zero',400,'thickness',0,'lgain',1.0, ...
   'pumpV',6,'valveV',12,'overshoot',0,'tol',2,'settle',5,'drainTo',0,'lead',3,'trimScale',0.7,'react',1,'hold',1,'low',80);
end
function [gain, intercept] = fit_tof_sweep(csvFile, minTrue, maxTrue)
T = readtable(csvFile);
k = T.true_mm >= minTrue & T.true_mm <= maxTrue;
p = polyfit(T.true_mm(k), T.measured_mm(k), 1);      % measured = gain*true + intercept
gain = p(1); intercept = p(2);
res = (T.measured_mm(k) - intercept) / gain - T.true_mm(k);
fprintf('measured = %.5f * true + %.3f   (worst residual %.2f mm, %d points)\n', ...
    gain, intercept, max(abs(res)), nnz(k));
end
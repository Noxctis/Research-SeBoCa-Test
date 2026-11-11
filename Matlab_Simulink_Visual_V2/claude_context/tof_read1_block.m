function d = tof_correct(dist, gain, intercept) %#codegen
% same formula as tofCorrect() in tof_cal.cpp: corrected = (raw - b) / m
if dist == 0
    d = 0;                        % no reading yet, pass through
else
    d = (double(dist) - intercept) / gain;
end
end
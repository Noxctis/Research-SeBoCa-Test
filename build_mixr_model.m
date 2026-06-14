% =========================================================================
% MIXR-1 Simulink Auto-Generator (Simulink Support Package Hardware Target)
% =========================================================================

modelName = 'water_level_model';

% 1. Initialize empty system canvas
try
    close_system(modelName, 0);
catch
end
new_system(modelName);
open_system(modelName);

% 2. Force loading of the correct hardware support package structures
disp('Registering Simulink Support Package for Raspberry Pi Hardware blocks...');
try
    % Load the core IO library which holds the Quadrature Encoder
    load_system('raspi_io_lib');
    encoderBlockPath = 'raspi_io_lib/Quadrature Encoder';
    fprintf('Targeting hardware block reference: %s\n', encoderBlockPath);
catch
    try
        % Legacy library fallback block path
        load_system('raspberrypilib');
        encoderBlockPath = 'raspberrypilib/Quadrature Encoder';
    catch
        error('CRITICAL: Raspberry Pi Support Package not found. Install it via Add-On Explorer.');
    end
end

% 3. Extract the Host PC IPv4 Address for automation
[~, ~] = system('hostname');
localIP = java.net.InetAddress.getLocalHost().getHostAddress();

% 4. Add Hardware & Routing Blocks
% Add the Official Quadrature Encoder Block
add_block(encoderBlockPath, [modelName, '/Motor_Encoder'], 'Position', [50, 100, 150, 150]);
set_param([modelName, '/Motor_Encoder'], 'PinA', '23', 'PinB', '24');
set_param([modelName, '/Motor_Encoder'], 'SampleTime', '0.1');

% Add the Ticks to RPM Math conversion block
add_block('simulink/Math Operations/Gain', [modelName, '/Ticks_to_RPM'], 'Position', [200, 105, 260, 145]);
set_param([modelName, '/Ticks_to_RPM'], 'Gain', '600/617.35');

% Add the continuous dummy torque source for Python dashboard pipeline alignment
add_block('simulink/Sources/Constant', [modelName, '/Dummy_Torque'], 'Position', [200, 180, 260, 210]);
set_param([modelName, '/Dummy_Torque'], 'Value', '0.0');

% Add the Vector Mux block
add_block('simulink/Signal Routing/Mux', [modelName, '/Data_Mux'], 'Position', [320, 100, 325, 220]);
set_param([modelName, '/Data_Mux'], 'Inputs', '2');

% Add the Dedicated Raspberry Pi TCP/IP Client block
add_block('raspi_io_lib/TCP//IP Client', [modelName, '/TCP_Client'], 'Position', [450, 135, 550, 185]);
set_param([modelName, '/TCP_Client'], 'Address', char(localIP));
set_param([modelName, '/TCP_Client'], 'Port', '5000');

% 5. Interconnect Routing Pins
add_line(modelName, 'Motor_Encoder/1', 'Ticks_to_RPM/1', 'autorouting', 'on');
add_line(modelName, 'Ticks_to_RPM/1', 'Data_Mux/1', 'autorouting', 'on');
add_line(modelName, 'Dummy_Torque/1', 'Data_Mux/2', 'autorouting', 'on');
add_line(modelName, 'Data_Mux/1', 'TCP_Client/1', 'autorouting', 'on');

% 6. Target Target Hardware Execution Engine Properties
set_param(modelName, 'SolverType', 'Fixed-step');
set_param(modelName, 'FixedStep', '0.1'); 
set_param(modelName, 'SystemTargetFile', 'ert.tlc'); 
set_param(modelName, 'HardwareBoard', 'Raspberry Pi');

save_system(modelName);
disp('[MIXR-1] Hardware-linked block model constructed successfully.');
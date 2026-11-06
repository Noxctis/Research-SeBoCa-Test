function fc(varargin)
% fc(3)                          send command 3
% fc('target',80)                change the target
% fc(3,'target',80,'pumpV',6)    several at once
% fc('clear')                    go back to the Constant block values
% names: cmd target pumpV valveV drainTo overshoot tol settle zero thickness lgain
host = 'mixr1.local';            % use the Pi's IP address if this name doesn't resolve
port = 25000;

msg = '';
i = 1;
while i <= numel(varargin)
    a = varargin{i};
    if isnumeric(a)
        msg = [msg sprintf(' cmd=%g', a)];  i = i + 1;
    elseif strcmpi(char(a), 'clear')
        msg = [msg ' clear'];               i = i + 1;
    else
        msg = [msg sprintf(' %s=%g', char(a), varargin{i+1})];  i = i + 2;
    end
end
msg = strtrim(msg);

try
    persistent sock
    if isempty(sock), sock = java.net.DatagramSocket(); end
    addr = java.net.InetAddress.getByName(host);
    data = int8(msg);
    pkt  = java.net.DatagramPacket(data, numel(data), addr, port);
    sock.send(pkt);
catch err
    % fallback without Java: slower (about half a second) but needs no toolbox
    ps = sprintf(['powershell -NoProfile -Command "$u=New-Object System.Net.Sockets.UdpClient; ' ...
        '$b=[Text.Encoding]::ASCII.GetBytes(''%s''); [void]$u.Send($b,$b.Length,''%s'',%d)"'], msg, host, port);
    [stt, out] = system(ps);
    if stt ~= 0
        error('fc:send', 'Could not send (%s). Output: %s', err.message, out);
    end
end
fprintf('sent: %s\n', msg);
end
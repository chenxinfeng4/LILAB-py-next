function t2c_realtime_position_client_socket()
    tcp_socket = tcpclient('10.50.60.6', 8090);
    cmds ={'hello', 'com3d', 'ba_poses'};
    response = send_read(tcp_socket, '404');
    disp(char(response))
    disp('----')
    a = tic;
    for i = 1:numel(cmds)
        send_data=cmds{i};
        response = send_read(tcp_socket, send_data);
        dt = toc(a);
        disp([send_data, ' took ', num2str(dt), ' seconds'])
        disp(char(response))
        disp('----')
        pause(5)
        a = tic;
    end
end


function response_msg = send_read(tcp_socket, send_data)
    writeline(tcp_socket, send_data);
    response_msg = readline(tcp_socket);
end

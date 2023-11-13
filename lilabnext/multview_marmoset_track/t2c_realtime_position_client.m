url = 'http://127.0.0.1:8089/';
response = webread(url);
C = strsplit(response, '\t');
date_str = C{1};
posi = strtrim(C{2});

t = datetime(date_str, 'InputFormat', 'yyyy-MM-dd HH:mm:ss.SSS');
year = year(t);
month = month(t);
day = day(t);
hour = hour(t);
minute = minute(t);
second_float = second(t);

disp('Timestamp parse')
disp([year,month,day,hour,minute,second_float])

disp('Position parse')
disp(posi)

t_stamp_sec_dot_milli = convertTo(t, 'posixtime');
fprintf('%.6f\n', t_stamp_sec_dot_milli)

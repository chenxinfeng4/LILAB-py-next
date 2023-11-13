#!/usr/bin/env python3
import requests
import datetime


url = "http://10.50.60.6:8089/com3d"

response = requests.get(url)
print(response.text)


date_str, posi = response.text.split("\t")
posi = posi.strip()
t = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
print('时间戳解析', t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)
print('位置戳解析', posi)

t_stamp_sec_dot_milli = t.timestamp() #the number of seconds since 1970-1-1, UTC
print('时间戳秒', t_stamp_sec_dot_milli)

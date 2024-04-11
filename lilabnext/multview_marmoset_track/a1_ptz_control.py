# from lilabnext.multview_marmoset_track.a1_ptz_control import status
import requests
import sys
import re
from requests.auth import HTTPDigestAuth
from typing import Tuple
import argparse

# ip = '10.50.5.252'
# port = '8081'
ip = '192.168.1.210'
port = '80'
username = 'admin'
password = '2019Cibr'

pan, tilt, zoom = ['0', '150', '10']  # 替换为你的实际值

auth = HTTPDigestAuth(username, password)
headers = {'Content-Type': 'application/xml'}


def control(pan, tilt, zoom, ip=ip, port=port):
    xml_data = f'''
    <PTZData xmlns="http://www.hikvision.com/ver20/XMLSchema">
        <AbsoluteHigh>
            <elevation>{tilt}</elevation>
            <azimuth>{pan}</azimuth>
            <absoluteZoom>{zoom}</absoluteZoom>
        </AbsoluteHigh>
    </PTZData>
    '''
    url = f'http://{ip}:{port}/ISAPI/PTZCtrl/channels/1/absolute'
    response = requests.put(url, headers=headers, data=xml_data, auth=auth)

    if response.status_code == 200:
        # print(response.text)
        pass
    else:
        print(f"Request failed with status code: {response.status_code}")
    return response.text

def control_PTZF(pan:float, tilt:float, zoom:float, focus:int, ip=ip, port=port):
    pan_float = round(pan, 2)
    tilt_float = round(tilt, 2)
    zoom_float = round(zoom, 1)
    focus = int(focus)
    xml_data = f'''
    <?xml version="1.0" encoding="UTF-8"?>
    <PTZAbsoluteEx version="2.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
        <elevation>{tilt_float}</elevation>
        <azimuth>{pan_float}</azimuth>
        <absoluteZoom>{zoom_float}</absoluteZoom>
        <focus>{focus}</focus>
        <horizontalSpeed>1</horizontalSpeed>
        <verticalSpeed>1</verticalSpeed>
        <zoomType>absoluteZoom</zoomType>
        <isContinuousTrackingEnabled>true</isContinuousTrackingEnabled>
    </PTZAbsoluteEx>
    '''
    url = f'http://{ip}:{port}/ISAPI/PTZCtrl/channels/1/absoluteEx'
    response = requests.put(url, headers=headers, data=xml_data, auth=auth)

    if response.status_code == 200:
        # print(response.text)
        pass
    else:
        print(xml_data)
        print(response.text)
        print(f"Request failed with status code: {response.status_code}")
    return response.text


def status(ip=ip, port=port) -> list:
    url = f'http://{ip}:{port}/ISAPI/PTZCtrl/channels/1/status'
    response = requests.get(url, auth=auth, verify=False)
    if response.status_code == 200:
        xml_string = response.text
        pan = int(re.search(r'<azimuth>(.*?)</azimuth>', xml_string).group(1))
        tilt = int(re.search(r'<elevation>(.*?)</elevation>', xml_string).group(1))
        zoom = int(re.search(r'<absoluteZoom>(.*?)</absoluteZoom>', xml_string).group(1))
    else:
        print(f"Request failed with status code: {response.status_code}")
        tilt = pan = zoom = 0
    return pan, tilt, zoom


def status_PTZF(ip=ip, port=port) -> Tuple[float, float, float, int]:
    url = f'http://{ip}:{port}/ISAPI/PTZCtrl/channels/1/absoluteEx'
    response = requests.get(url, auth=auth, verify=False)
    if response.status_code == 200:
        xml_string = response.text
        pan =  round(float(re.search(r'<azimuth>(.*?)</azimuth>', xml_string).group(1)), 2)
        tilt = round(float(re.search(r'<elevation>(.*?)</elevation>', xml_string).group(1)), 2)
        zoom = round(float(re.search(r'<absoluteZoom>(.*?)</absoluteZoom>', xml_string).group(1)), 1)
        focus = int(re.search(r'<focus>(.*?)</focus>', xml_string).group(1))
    else:
        print(f"Request failed with status code: {response.status_code}")
        tilt = pan = zoom = focus =  0
    return pan, tilt, zoom, focus


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='PTZ control for Marmoset Tracker')
    parser.add_argument('--ip', type=str, default=ip)
    parser.add_argument('--port', type=str, default=port)
    parser.add_argument('--getPTZF', action='store_true')
    parser.add_argument('--getPTZ',  action='store_true')
    parser.add_argument('--setPTZF', action='store_true')
    parser.add_argument('--setPTZ',  action='store_true')
    parser.add_argument('PTZF', nargs='*', type=float, default=[0, 0, 0, 0])
    args = parser.parse_args()

    assert args.getPTZF + args.getPTZ + args.setPTZF + args.setPTZ == 1, 'Please specify exactly one action.'
    ip_now = args.ip
    port_now = args.port
    if args.getPTZF:
        pan, tilt, zoom, focus = status_PTZF(ip_now, port_now)
        print(f'Pan: {pan} \nTilt: {tilt} \nZoom: {zoom} \nFocus: {focus}')
    elif args.getPTZ:
        pan, tilt, zoom = [x/10 for x in status(ip_now, port_now)]
        print(f'Pan: {pan} \nTilt: {tilt} \nZoom: {zoom}')
    elif args.setPTZF:
        control_PTZF(*args.PTZF, ip_now, port_now)
    elif args.setPTZ:
        control(*[int(x*10) for x in args.PTZF], ip_now, port_now)
    else:
        raise ValueError('Should not reach here.')
    
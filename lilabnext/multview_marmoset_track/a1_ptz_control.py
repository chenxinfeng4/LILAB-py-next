# from lilabnext.multview_marmoset_track.a1_ptz_control import status
import requests
import sys
import re
from requests.auth import HTTPDigestAuth


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

def control_focus(focus, ip=ip, port=port):
    url = f'http://{ip}:{port}/ISAPI/System/Video/inputs/channels/1/focus'
    xml_data = f'<FocusData><focus>{focus}</focus></FocusData>'
    headers = {'Content-Type': 'application/xml'}
    auth = ('admin', '2019Cibr')
    response = requests.put(url, headers=headers, data=xml_data, auth=auth)


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


if __name__=='__main__':
    if len(sys.argv) == 4:
        pan = sys.argv[1]
        tilt = sys.argv[2]
        zoom = sys.argv[3]
        control(pan, tilt, zoom)
    else:
        print(status())
        print("Usage: python3 pan_tilt.py pan tilt zoom")
    
    

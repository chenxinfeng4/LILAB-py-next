import requests
import sys

ip = '10.50.5.252'
port = '8081'

username = 'admin'
password = '2019Cibr'

pan = '0'  # 替换为你的实际值
tilt = '0'  # 替换为你的实际值
zoom = '10'  # 替换为你的实际值

auth = (username, password)
url = f'http://{ip}:{port}/ISAPI/PTZCtrl/channels/1/absolute'
headers = {'Content-Type': 'application/xml'}


def control(pan, tilt, zoom):
    xml_data = f'''
    <PTZData xmlns="http://www.hikvision.com/ver20/XMLSchema">
        <AbsoluteHigh>
            <elevation>{tilt}</elevation>
            <azimuth>{pan}</azimuth>
            <absoluteZoom>{zoom}</absoluteZoom>
        </AbsoluteHigh>
    </PTZData>
    '''
    response = requests.put(url, headers=headers, data=xml_data, auth=auth)

    if response.status_code == 200:
        print(response.text)
    else:
        print(f"Request failed with status code: {response.status_code}")
    return response.text


if __name__=='__main__':
    if len(sys.argv) == 4:
        pan = sys.argv[1]
        tilt = sys.argv[2]
        zoom = sys.argv[3]
    else:
        print("Usage: python3 pan_tilt.py pan tilt zoom")
    
    control(pan, tilt, zoom)

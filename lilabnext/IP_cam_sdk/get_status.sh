ip=192.168.1.210
port=80
USERNAME=admin
PASSWORD=2019Cibr



# 获取PTZ
curl http://$ip:$port//ISAPI/PTZCtrl/channels/1/status  --digest  --user "${USERNAME}:${PASSWORD}"

pan=615
tilt=266
zoom=19

xml_data=$(cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<PTZData xmlns="http://www.hikvision.com/ver20/XMLSchema">
    <AbsoluteHigh>
        <elevation>${tilt}</elevation>
        <azimuth>${pan}</azimuth>
        <absoluteZoom>${zoom}</absoluteZoom>
    </AbsoluteHigh>
</PTZData>
EOF
)
curl -u "${USERNAME}:${PASSWORD}" -X PUT  --digest -H "Content-Type: application/xml" \
    -d "${xml_data}" "http://${ip}:${port}/ISAPI/PTZCtrl/channels/1/absolute" 



# 获取和设置PTZF，推荐
curl http://$ip:$port//ISAPI/PTZCtrl/channels/1/absoluteEx  --digest  --user "${USERNAME}:${PASSWORD}" #推荐

tilt=60.76
pan=267.47
zoom=1
focus=28704

url="http://${ip}:${port}/ISAPI/PTZCtrl/channels/1/absolute"
xml_data=$(cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<PTZAbsoluteEx version="2.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
    <elevation>$tilt</elevation>
    <azimuth>$pan</azimuth>
    <absoluteZoom>$zoom</absoluteZoom>
    <focus>$focus</focus>
    <horizontalSpeed>1</horizontalSpeed>
    <verticalSpeed>1</verticalSpeed>
    <zoomType>absoluteZoom</zoomType>
    <isContinuousTrackingEnabled>true</isContinuousTrackingEnabled>
</PTZAbsoluteEx>
EOF
)
curl -u "${USERNAME}:${PASSWORD}" -X PUT  --digest -H "Content-Type: application/xml" \
    -d "${xml_data}" "http://${ip}:${port}/ISAPI/PTZCtrl/channels/1/absoluteEx" 

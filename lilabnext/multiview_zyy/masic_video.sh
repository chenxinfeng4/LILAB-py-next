V="08-14-23-17-05-20.000"

ffmpeg -i $V-1c.avi -i $V-2c.avi -i $V-3c.avi -i $V-4c.avi -i $V-5c.avi -i $V-6c.avi \
    -filter_complex "[0:v][1:v][2:v][3:v][4:v][5:v]xstack=inputs=6:layout=0_0|w0_0|w0+w0_0|0_h0|w0_h0|w0+w0_h0" \
    -r 30 -c:v hevc_nvenc -b:v 8M -y 1_6grid_checkboard.mp4
 
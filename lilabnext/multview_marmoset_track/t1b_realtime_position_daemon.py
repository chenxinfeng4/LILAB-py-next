# curl http://127.0.0.1:8089
# python -m lilabnext.multview_marmoset_track.t1b_realtime_position_daemon
from flask import Flask
from .msg_file_io import read_msg, read_calibpkl_msg

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def greeting():
    msg = 'Welcome to the marmoset tracker!\n'
    return msg


@app.route("/com3d", methods=["GET", "POST"])
def get_com3d():
    msg = read_msg()
    return msg

@app.route("/ba_poses", methods=["GET", "POST"])
def get_ba_poses():
    msg = read_calibpkl_msg()
    return msg

@app.route('/parent/child', methods=['GET'])
def child_get_route():
    return 'This is the GET route for the child path'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8089, debug=True)
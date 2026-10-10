"""Record only the RViz window of a fresh Gazebo run, not the whole desktop.

Requires GStreamer (ximagesrc, x264enc, mp4mux) and xwininfo. On a Wayland
session RViz must run through XWayland, as it does on the tested Ubuntu setup.
"""
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

package = Path(__file__).resolve().parents[1]
workspace = package.parents[1]
output = package / 'results/recording'
output.mkdir(parents=True, exist_ok=True)
report = output / 'result.json'
if report.exists():
    report.unlink()
world = workspace / 'install/ros_gz_crazyflie_gazebo/share/ros_gz_crazyflie_gazebo/worlds/crazyflie_world.sdf'


def rviz_windows():
    tree = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
    windows = set()
    for line in tree.splitlines():
        if 'rviz' not in line.lower():
            continue
        identity = re.search(r'0x[0-9a-f]+', line)
        size = re.search(r'(\d+)x(\d+)[+-]', line)
        # Qt also creates an invisible 1x1 helper window. Do not record it.
        if identity and size and int(size[1]) > 500 and int(size[2]) > 300:
            windows.add(identity[0])
    return windows


def stop(process):
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)


existing_windows = rviz_windows()
environment = dict(os.environ, ROS_DOMAIN_ID='103', GZ_PARTITION='capstone_recording',
                   DEMO_OUTPUT_DIR=str(output), QT_QPA_PLATFORM='xcb')
launch_command = [
    'bash', str(package / 'scripts/run_demo.sh'),
    'gz_args:=' + str(world) + ' -s -r', 'startup_delay:=15.0']
recording = None
with (output / 'simulation.log').open('w') as simulation_log, (output / 'capture.log').open('w') as capture_log:
    simulation = subprocess.Popen(launch_command, env=environment,
                                  stdout=simulation_log, stderr=subprocess.STDOUT,
                                  start_new_session=True)
    try:
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            new_windows = rviz_windows() - existing_windows
            if new_windows:
                window = sorted(new_windows)[0]
                break
            if simulation.poll() is not None:
                raise RuntimeError('Simulation exited before RViz appeared.')
            time.sleep(0.25)
        else:
            raise RuntimeError('No new RViz X11 window found. Check XWayland.')

        time.sleep(3)  # Allow the new window to be mapped before capture.
        pipeline = [
            'gst-launch-1.0', '-e', 'ximagesrc', 'xid=' + str(int(window, 16)),
            'use-damage=false', 'remote=true', 'show-pointer=false', '!',
            'video/x-raw,framerate=20/1', '!', 'videoconvert', '!',
            'video/x-raw,format=I420', '!',
            'x264enc', 'tune=zerolatency', 'speed-preset=ultrafast', 'bitrate=2500',
            '!', 'video/x-h264,stream-format=avc,alignment=au', '!', 'mp4mux', '!', 'filesink',
            'location=' + str(output / 'waypoint_demo.mp4')]
        recording = subprocess.Popen(pipeline, stdout=capture_log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
        print('Recording the actual RViz window. Leave this window open.', flush=True)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if recording.poll() is not None:
                raise RuntimeError('Video capture stopped unexpectedly; see capture.log.')
            if report.exists():
                result = json.loads(report.read_text())
                if not result['passed']:
                    raise RuntimeError('Flight did not pass; no successful demo claimed.')
                time.sleep(4)
                break
            time.sleep(0.5)
        else:
            raise RuntimeError('Flight timed out.')

        # A real final frame, after landing, for the README or email.
        subprocess.run([
            'gst-launch-1.0', '-q', 'ximagesrc', 'xid=' + str(int(window, 16)),
            'num-buffers=1', 'use-damage=false', 'remote=true', 'show-pointer=false', '!',
            'videoconvert', '!', 'pngenc', '!', 'filesink',
            'location=' + str(output / 'rviz_final.png')], check=True, timeout=15)
    finally:
        # EOS finalizes the MP4 before the window is closed.
        stop(recording)
        stop(simulation)

subprocess.run(['python3', str(package / 'scripts/plot_flight.py'),
                str(output / 'flight.csv')], check=True)
print('Saved actual window video, screenshot, CSV, result and plots to ' + str(output), flush=True)

# Recording the demo

The example video is an actual RViz capture during a live Gazebo simulation.
It is not a rendered animation made from invented coordinates. RViz displays
Gazebo odometry and the commands produced by the running ROS nodes.

## Watch

[Download the demo MP4](media/waypoint_demo.mp4)

The cyan line is the measured path, the orange line connects the requested
waypoints, and the small axes mark the current simulated drone position.
The text shows the stage and position in metres. Gazebo's physics server runs
in the background during recording; the video shows RViz, not Gazebo's GUI.
There is no audio.

## Record another run

On the tested Ubuntu desktop, GStreamer and XWayland can capture only the RViz
window. The script ignores the small hidden windows created by Qt.

```bash
source /opt/ros/humble/setup.bash
source install/local_setup.bash
python3 src/capstone_demo/scripts/record_demo.py
```

Run these commands from the ROS workspace. The script waits 15 simulation
seconds before the first waypoint so the recorder can start. It stops after
landing, keeps four seconds of the completed path, and finalizes the MP4.
Only the RViz rendering window is captured, not the full desktop.

Outputs are in `results/recording/`:

- `waypoint_demo.mp4`: H.264 MP4 screen recording.
- `rviz_final.png`: actual final-window screenshot.
- `flight.csv`: target and measured positions from this same run.
- `result.json`: measured arrival errors and completion status.
- `position_tracking.png`, `flight_path.png`: plots made from the CSV.

The script needs `xwininfo`, GStreamer tools, ximagesrc, x264enc and mp4mux.
On a machine without them, the relevant Ubuntu packages are `x11-utils`,
`gstreamer1.0-tools`, `gstreamer1.0-x`, `gstreamer1.0-plugins-good`, and
`gstreamer1.0-plugins-ugly`.

Keep RViz open and on the visible desktop while recording. A native Wayland
RViz window needs a different screen-capture backend; this script explicitly
starts RViz with Qt's X11 backend.

For a useful presentation, show the video first, then the position plot,
then the small control equation in `controller.py`. The plot explains the
controller more clearly than a video alone.

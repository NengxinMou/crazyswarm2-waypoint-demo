# Crazyflie waypoint demo

A small ROS 2 practice project in Gazebo. The drone takes off to 1 m,
moves 1 m along the y axis, and lands.

[Demo video](docs/media/waypoint_demo.mp4)

## How it works

- `trajectory_planner.py` sends the waypoints one at a time.
- `controller.py` reads the current position and calculates a velocity command.
- `gazebo_adapter.py` passes commands and position feedback between ROS and Gazebo.

The position controller is a P controller:

```text
velocity = Kp * (target position - current position)
```

The default gain is 0.9, with limits on the commanded velocity. The planner
switches to the next point after staying within 7 cm of the target for 2 seconds.

This demo uses the Crazyswarm2 `FullState` message type. The adapter uses its
velocity fields to drive Gazebo's built-in velocity controller; it does not run
`crazyflie_server` or the firmware full-state controller.

## Run

Tested with Ubuntu 22.04, ROS 2 Humble and Gazebo Harmonic.
Install ROS Humble Desktop and Gazebo Harmonic first, then these dependencies
(use the Harmonic ROS bridge):

```bash
sudo apt install python3-colcon-common-extensions python3-vcstool \
  libboost-program-options-dev libusb-1.0-0-dev libeigen3-dev \
  ros-humble-motion-capture-tracking ros-humble-tf-transformations \
  ros-humble-ros-gzharmonic python3-yaml python3-matplotlib
```

To build in a new directory:

```bash
mkdir -p crazyflie_demo/ros2_ws/src
cd crazyflie_demo
git clone https://github.com/NengxinMou/crazyswarm2-waypoint-demo.git ros2_ws/src/capstone_demo
vcs import --recursive . < ros2_ws/src/capstone_demo/dependencies.repos
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to capstone_demo \
  --cmake-args -DBUILD_TESTING=OFF
bash src/capstone_demo/scripts/run_demo.sh
```

For later runs, use the last command from `ros2_ws`.

RViz shows the target and actual paths. Press Ctrl+C to stop after landing.

Edit `config/assignment.yaml` to change the waypoints. A small square example
is also included in `config/square.yaml`. Positions are `[x, y, z]` in metres;
the last point should have z = 0 for landing.

## Notes

The takeoff–move–land sequence and the square example have been tested in
simulation. The video shows the flight path in RViz while Gazebo runs in the
background. Next I want to try more waypoints and learn about PID control.

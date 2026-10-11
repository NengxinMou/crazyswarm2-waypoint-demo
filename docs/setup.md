# Setup and experiment notes

A small ROS 2 learning project: take off to 1 m, move 1 m along +y, and land.
The controller uses position feedback and proportional (P) control.

[Watch/download the actual demo recording](media/waypoint_demo.mp4) | [Code walkthrough](walkthrough.md)

![Measured position tracking](position_tracking.png)

## What the code does

There are two application nodes:

- `trajectory_planner.py` publishes the next target on `/cf1/desired_state`.
- `controller.py` compares that target with `/cf1/pose` and publishes `/cf1/cmd_full_state`.

There is also a **Gazebo adapter node**, plus the standard ROS/Gazebo bridge.
The adapter converts simulator odometry into the position feedback and forwards
velocity commands to the model. It also publishes the path displayed in RViz.
These are additional nodes, not part of the two-node planner/controller split.

```text
trajectory_planner -- desired_state --> controller -- cmd_full_state --> gazebo_adapter
                                            ^                                |
                                            | pose                           | velocity
                                            +-------- gazebo_adapter <---- Gazebo
```

The position controller uses the same calculation on each axis:

```text
error = target position - measured position
requested velocity = Kp * error
```

`Kp` is 0.9 per second. Horizontal commands are limited to 0.25 m/s per axis;
vertical commands are limited to 0.30 m/s. Missing target or position updates
cause the command to return to zero after 0.5 seconds.

The planner waits until the 3D position error is below 0.07 m for 2 seconds
before moving to the next waypoint. The model's centre stays slightly above
z = 0 when touching the floor.

## Simulation interface

This project uses the Crazyswarm2 `FullState` message type, but **does not run
`crazyflie_server` or the Crazyflie firmware full-state controller**.
The installed Gazebo model has its own inner velocity/attitude controller.
Our adapter reads only `FullState.twist`; it does not implement position or
acceleration feedforward from the other fields. This is a simulator-specific
interface and is not a drop-in hardware controller.

## Tested environment

- Ubuntu 22.04, ROS 2 Humble
- Gazebo Harmonic (gz-sim 8), with `ros-humble-ros-gzharmonic`
- Crazyswarm2 message definitions
- `ros_gz_crazyflie` world and Bitcraze `crazyflie-simulation` model

See `dependencies.repos` for the exact source revisions used. Upstream source
code is kept in its own repositories rather than copied into this project.

## Build and run

Use this directory layout:

```text
crazyflie_demo/
  ros2_ws/
    src/
      capstone_demo/             # this repository
      crazyswarm2/
      ros_gz_crazyflie/
  simulation_ws/
    crazyflie-simulation/
```

First install ROS Humble Desktop and Gazebo Harmonic using their official
instructions. The ROS/Gazebo bridge must be the **Harmonic** package, not the
default Humble/Fortress bridge. Then install the development dependencies:

```bash
sudo apt install python3-colcon-common-extensions python3-vcstool \
  libboost-program-options-dev libusb-1.0-0-dev libeigen3-dev \
  ros-humble-motion-capture-tracking ros-humble-tf-transformations \
  ros-humble-ros-gzharmonic python3-yaml python3-matplotlib
```

Place this repository at `crazyflie_demo/ros2_ws/src/capstone_demo`. From the
`crazyflie_demo` directory, import the pinned dependencies:

```bash
vcs import --recursive . < ros2_ws/src/capstone_demo/dependencies.repos
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to capstone_demo \
  --cmake-args -DBUILD_TESTING=OFF
bash src/capstone_demo/scripts/run_demo.sh
```

The script loads the workspace and model path. RViz shows the planned path in
orange and the measured path in cyan. The status label shows the current stage
and actual position. The simulation stays open after landing. Stop with Ctrl+C
before starting another run.

If the models are stored elsewhere, set `CF_SIM_MODEL_DIR` to their
`simulator_files/gazebo` directory. On an NVIDIA hybrid-graphics laptop, these
settings may be needed before starting RViz:

```bash
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
```

## Change the waypoints

Edit `config/assignment.yaml`. Positions are `[x, y, z]` in metres, in the world
frame. The last waypoint must be at z = 0 so the demo finishes with a landing.
Keep points inside the simulation world. This is discrete waypoint following,
not a time-parameterized trajectory or obstacle-avoidance planner.

A small square is provided as a first additional experiment:

```bash
bash src/capstone_demo/scripts/run_demo.sh \
  waypoint_file:="$(pwd)/src/capstone_demo/config/square.yaml"
```

To try a different proportional gain:

```bash
bash src/capstone_demo/scripts/run_demo.sh kp:=0.7
```

## Results and recording

Each run writes `flight.csv` (target and measured positions) and `result.json`
(arrival errors) under `results/latest`. Set `DEMO_OUTPUT_DIR` to keep runs in
separate directories.

```bash
python3 src/capstone_demo/scripts/plot_flight.py \
  src/capstone_demo/results/latest/flight.csv
```

The plotted error during a waypoint switch is expected: a new target is set
before the drone has travelled to it. Arrival error is measured separately
once the drone has remained within tolerance for 2 seconds.

See [recording instructions](recording.md) for the actual RViz window
capture and [test results](results.md) for measured runs.

To inspect topics in another terminal, use the same ROS domain as the launcher
(default 96):

```bash
ROS_DOMAIN_ID=96 ros2 topic echo /cf1/desired_state
ROS_DOMAIN_ID=96 ros2 topic echo /cf1/pose
ROS_DOMAIN_ID=96 ros2 topic echo /cf1/cmd_full_state
```

## Next steps

- Try more waypoint layouts and compare measured paths.
- Study PID control and compare a PID controller with this P baseline.
- Understand the `crazyflie_server` interface before changing backends.

## References

- [Bitcraze ROS 2 and Gazebo tutorial](https://www.bitcraze.io/2024/09/crazyflies-adventures-with-ros-2-and-gazebo/)
- [Crazyswarm2](https://github.com/IMRCLab/crazyswarm2)
- [ROS/Gazebo Crazyflie integration](https://github.com/knmcguire/ros_gz_crazyflie)
- [Crazyflie simulation models](https://github.com/bitcraze/crazyflie-simulation)
- [ROS Humble installation](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)
- [Gazebo Harmonic installation](https://gazebosim.org/docs/harmonic/install_ubuntu/)

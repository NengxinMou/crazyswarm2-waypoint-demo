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
See [setup instructions](docs/setup.md#build-and-run) for dependencies and building.

From the ROS workspace (`ros2_ws`):

```bash
bash src/capstone_demo/scripts/run_demo.sh
```

RViz shows the target and actual paths. Press Ctrl+C to stop after landing.

Edit `config/assignment.yaml` to change the waypoints. A small square example
is also included in `config/square.yaml`.

## Notes

The takeoff–move–land sequence and the square example have been tested in
simulation. Next I want to try more waypoints and learn about PID control.

[Code notes](docs/walkthrough.md) · [Test results](docs/results.md) · [Recording instructions](docs/recording.md)

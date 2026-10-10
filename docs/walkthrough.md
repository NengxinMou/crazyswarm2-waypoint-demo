# How to explain this project

## 1. Where do the target positions come from?

`config/assignment.yaml` contains three positions: `[0, 0, 1]`, `[0, 1, 1]`,
and `[0, 1, 0]`. The planner sends one target at a time. Units are metres and
the axes belong to the simulation world.

## 2. What does the planner do?

Every 0.1 seconds, it publishes the current target and checks the measured
position. If the drone stays within 7 cm of the target for 2 seconds, it
advances to the next target. It does not calculate motor commands.

## 3. What does the controller do?

Every 0.05 seconds, it calculates three position errors. For example:

```python
error_z = target.position.z - pose.position.z
velocity_z = kp * error_z
```

A positive vertical error requests upward velocity. A negative error requests
downward velocity. Close to the target, the requested velocity becomes small.
The result is limited so a distant target does not request excessive speed.

## 4. Is this PID?

No. It is P control only. There is no integral accumulator and no derivative
term. PID is a possible next experiment, not something already implemented.

## 5. Where does the measured position come from?

Gazebo publishes simulated odometry. The ROS/Gazebo bridge transfers it to
`/cf1/odom`. The adapter republishes the pose as `/cf1/pose` for the controller
and planner. This is simulator feedback, not a real-world position estimate.

## 6. How many nodes are there?

Two application nodes handle planning and position control. A third custom
node adapts the simulator interface and displays the path. The standard bridge
and RViz also run. One launch command starts all of them; one command does
not mean one node.

## 7. Does FullState go directly to Crazyflie firmware?

No. We use the Crazyswarm2 message type to keep the assignment's output topic.
The Gazebo adapter reads its velocity field and sends that to the model's
velocity controller. Gazebo's built-in controller handles attitude and motors.
The firmware full-state backend and `crazyflie_server` are not running here.

## 8. What has been measured?

The CSV logs target and actual x/y/z positions. The JSON records the position
error at each confirmed arrival. The 7 cm arrival threshold is a condition for
advancing, not a claim that the error is always below 7 cm while travelling.

## 9. How do I try another route?

Change the YAML waypoints, keeping them inside the world and ending at z = 0.
The square example is a first experiment. This code does not interpolate a
time-based trajectory or avoid obstacles.

## 10. What would I improve next?

Compare gains, test more paths, then study integral/derivative terms and decide
whether PID improves measured tracking. Keep the current P run as a baseline.

"""Send waypoints in order and record the measured positions."""

import csv
import json
import math
from pathlib import Path
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path as FlightPath
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import String
import yaml


class TrajectoryPlanner(Node):
    def __init__(self):
        super().__init__('trajectory_planner')
        self.declare_parameter('waypoint_file', '')
        self.declare_parameter('output_dir', '/tmp/capstone-demo')
        self.declare_parameter('startup_delay', 4.0)
        self.startup_delay = self.get_parameter('startup_delay').value
        self.tolerance = 0.07  # metres
        self.hold_time = 2.0   # seconds inside the tolerance

        waypoint_file = self.get_parameter('waypoint_file').value
        with open(waypoint_file) as stream:
            self.waypoints = yaml.safe_load(stream)['waypoints']
        self.check_waypoints()

        self.output_dir = Path(self.get_parameter('output_dir').value)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = (self.output_dir / 'flight.csv').open('w', newline='')
        self.csv_writer = csv.writer(self.csv_file, lineterminator='\n')
        self.csv_writer.writerow([
            'time_s', 'stage', 'target_x', 'target_y', 'target_z',
            'actual_x', 'actual_y', 'actual_z', 'error_m'])

        self.target_publisher = self.create_publisher(
            PoseStamped, '/cf1/desired_state', 10)
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.state_publisher = self.create_publisher(String, '/cf1/mission_state', latched)
        self.path_publisher = self.create_publisher(FlightPath, '/cf1/planned_path', latched)
        self.create_subscription(PoseStamped, '/cf1/pose', self.receive_pose, 10)

        self.pose = None
        self.pose_received_at = 0.0
        self.start_time = None
        self.inside_since = None
        self.stage_started_at = None
        self.index = 0
        self.results = []
        self.finished = False
        self.last_state = ''
        self.create_timer(0.1, self.update_plan)

    def check_waypoints(self):
        if not isinstance(self.waypoints, list) or not self.waypoints:
            raise ValueError('Provide at least one waypoint.')
        for waypoint in self.waypoints:
            position = waypoint['position']
            if len(position) != 3 or not all(math.isfinite(v) for v in position):
                raise ValueError('Each position needs three finite numbers: x, y, z.')
            if position[2] < 0:
                raise ValueError('Waypoint height cannot be negative.')
        if self.waypoints[-1]['position'][2] != 0:
            raise ValueError('End this demo with a landing waypoint at z = 0.')

    def receive_pose(self, message):
        self.pose = message.pose.position
        self.pose_received_at = time.monotonic()

    def publish_state(self, state):
        self.state_publisher.publish(String(data=state))
        if state != self.last_state:
            self.get_logger().info(state)
            self.last_state = state

    def make_pose(self, position):
        message = PoseStamped()
        message.header.frame_id = 'world'
        message.header.stamp = self.get_clock().now().to_msg()
        message.pose.position.x = float(position[0])
        message.pose.position.y = float(position[1])
        message.pose.position.z = float(position[2])
        message.pose.orientation.w = 1.0
        return message

    def publish_planned_path(self):
        path = FlightPath()
        path.header.frame_id = 'world'
        path.header.stamp = self.get_clock().now().to_msg()
        path.poses = [self.make_pose([0, 0, 0])]
        for waypoint in self.waypoints:
            path.poses.append(self.make_pose(waypoint['position']))
        self.path_publisher.publish(path)

    def update_plan(self):
        if self.finished:
            return
        if self.pose is None or time.monotonic() - self.pose_received_at > 0.5:
            self.inside_since = None
            return

        now = self.get_clock().now().nanoseconds / 1e9
        if self.start_time is None:
            self.start_time = now
            self.publish_planned_path()
        if now - self.start_time < self.startup_delay:
            self.publish_state('WAITING')
            return

        waypoint = self.waypoints[self.index]
        target = waypoint['position']
        self.publish_state(waypoint['name'])
        self.target_publisher.publish(self.make_pose(target))
        if self.stage_started_at is None:
            self.stage_started_at = now

        actual = [self.pose.x, self.pose.y, self.pose.z]
        error = math.dist(target, actual)
        self.csv_writer.writerow([
            now - self.start_time, waypoint['name'], *target, *actual, error])
        self.csv_file.flush()

        if now - self.stage_started_at > 60.0:
            self.finish(False, 'Waypoint timed out')
            return

        if error < self.tolerance:
            if self.inside_since is None:
                self.inside_since = now
            if now - self.inside_since >= self.hold_time:
                self.results.append({
                    'stage': waypoint['name'], 'target': target,
                    'actual': actual, 'error_m': error,
                    'time_s': now - self.start_time})
                self.index += 1
                self.inside_since = None
                self.stage_started_at = None
                if self.index == len(self.waypoints):
                    self.finish(True, 'All waypoints reached')
        else:
            self.inside_since = None

    def finish(self, passed, reason):
        self.finished = True
        self.csv_file.close()
        report = {
            'passed': passed, 'reason': reason,
            'tolerance_m': self.tolerance, 'hold_time_s': self.hold_time,
            'stages': self.results}
        (self.output_dir / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        self.publish_state('COMPLETE' if passed else 'FAILED')


def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryPlanner()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.csv_file.close()
        node.destroy_node()
        rclpy.try_shutdown()

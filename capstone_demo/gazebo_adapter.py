"""Simulation plumbing for the Gazebo velocity-controlled Crazyflie model.

FullState.twist is used as a world-frame velocity request. The other FullState
fields are NOT tracked by this adapter; this is not the firmware backend.
"""

import math
import time

import rclpy
from crazyflie_interfaces.msg import FullState
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry, Path
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import Bool, String
from visualization_msgs.msg import Marker


class GazeboAdapter(Node):
    def __init__(self):
        super().__init__('gazebo_adapter')
        self.pose_publisher = self.create_publisher(PoseStamped, '/cf1/pose', 10)
        self.path_publisher = self.create_publisher(Path, '/cf1/path', 10)
        self.velocity_publisher = self.create_publisher(Twist, '/cf1/sim_velocity', 10)
        self.enable_publisher = self.create_publisher(Bool, '/cf1/sim_enable', 10)
        self.label_publisher = self.create_publisher(Marker, '/cf1/status_label', 10)
        self.create_subscription(Odometry, '/cf1/odom', self.receive_odometry, 10)
        self.create_subscription(FullState, '/cf1/cmd_full_state', self.receive_command, 10)
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(String, '/cf1/mission_state', self.receive_state, latched)

        self.path = Path()
        self.path.header.frame_id = 'world'
        self.command = Twist()
        self.command_received_at = 0.0
        self.yaw = 0.0
        self.state = 'WAITING'
        self.odometry_count = 0
        self.position = None
        self.create_timer(0.05, self.update_simulation)

    def receive_odometry(self, message):
        pose = PoseStamped()
        pose.header = message.header
        pose.header.frame_id = 'world'
        pose.pose = message.pose.pose
        self.position = pose.pose.position
        self.pose_publisher.publish(pose)

        q = pose.pose.orientation
        self.yaw = math.atan2(
            2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        self.odometry_count += 1
        if self.odometry_count % 5 == 0:
            self.path.header.stamp = pose.header.stamp
            self.path.poses.append(pose)
            self.path.poses = self.path.poses[-6000:]
            self.path_publisher.publish(self.path)

    def receive_command(self, message):
        self.command = message.twist
        self.command_received_at = time.monotonic()

    def receive_state(self, message):
        self.state = message.data

    def update_simulation(self):
        velocity = Twist()
        fresh = time.monotonic() - self.command_received_at < 0.5
        if self.state not in ('COMPLETE', 'FAILED') and fresh:
            # The position controller works in world coordinates. Gazebo wants
            # horizontal velocity relative to the drone's current heading.
            cosine = math.cos(self.yaw)
            sine = math.sin(self.yaw)
            velocity.linear.x = cosine * self.command.linear.x + sine * self.command.linear.y
            velocity.linear.y = -sine * self.command.linear.x + cosine * self.command.linear.y
            velocity.linear.z = self.command.linear.z
            velocity.angular.z = -0.8 * self.yaw
        self.velocity_publisher.publish(velocity)
        # Only switch motors off after a completed landing, not on a timeout.
        self.enable_publisher.publish(Bool(data=self.state != 'COMPLETE'))
        self.publish_label()

    def publish_label(self):
        label = Marker()
        label.header.frame_id = 'world'
        label.header.stamp = self.get_clock().now().to_msg()
        label.ns = 'status'
        label.id = 0
        label.type = Marker.TEXT_VIEW_FACING
        label.action = Marker.ADD
        label.pose.position.z = 1.65
        label.pose.position.y = 0.5
        label.pose.orientation.w = 1.0
        label.scale.z = 0.075
        label.color.r = label.color.g = label.color.b = label.color.a = 1.0
        label.text = 'P-control\n' + self.state
        if self.position is not None:
            p = self.position
            label.text += f'\nx={p.x:.2f}m\ny={p.y:.2f}m\nz={p.z:.2f}m'
        self.label_publisher.publish(label)


def main(args=None):
    rclpy.init(args=args)
    node = GazeboAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

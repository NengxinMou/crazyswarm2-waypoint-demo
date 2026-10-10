"""A P position controller that produces limited velocity commands."""

import time

import rclpy
from crazyflie_interfaces.msg import FullState
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node


def limit(value, maximum):
    return max(-maximum, min(maximum, value))


class PositionController(Node):
    def __init__(self):
        super().__init__('controller')
        self.declare_parameter('kp', 0.9)
        self.declare_parameter('max_horizontal_speed', 0.25)
        self.declare_parameter('max_vertical_speed', 0.30)
        self.kp = self.get_parameter('kp').value
        self.horizontal_limit = self.get_parameter('max_horizontal_speed').value
        self.vertical_limit = self.get_parameter('max_vertical_speed').value
        if min(self.kp, self.horizontal_limit, self.vertical_limit) <= 0:
            raise ValueError('The gain and speed limits must be positive.')

        self.target = None
        self.pose = None
        self.target_received_at = 0.0
        self.pose_received_at = 0.0
        self.timeout = 0.5

        self.create_subscription(
            PoseStamped, '/cf1/desired_state', self.receive_target, 10)
        self.create_subscription(
            PoseStamped, '/cf1/pose', self.receive_pose, 10)
        self.command_publisher = self.create_publisher(
            FullState, '/cf1/cmd_full_state', 10)
        self.create_timer(0.05, self.update_control)

    def receive_target(self, message):
        self.target = message.pose
        self.target_received_at = time.monotonic()

    def receive_pose(self, message):
        self.pose = message.pose
        self.pose_received_at = time.monotonic()

    def update_control(self):
        if self.target is None or self.pose is None:
            return

        command = FullState()
        command.header.stamp = self.get_clock().now().to_msg()
        command.header.frame_id = 'world'
        command.pose = self.target

        # A default Twist is zero. Stop if feedback or the target goes missing.
        now = time.monotonic()
        feedback_is_fresh = now - self.pose_received_at < self.timeout
        target_is_fresh = now - self.target_received_at < self.timeout
        if feedback_is_fresh and target_is_fresh:
            error_x = self.target.position.x - self.pose.position.x
            error_y = self.target.position.y - self.pose.position.y
            error_z = self.target.position.z - self.pose.position.z

            # P control: requested velocity = gain * position error.
            command.twist.linear.x = limit(self.kp * error_x, self.horizontal_limit)
            command.twist.linear.y = limit(self.kp * error_y, self.horizontal_limit)
            command.twist.linear.z = limit(self.kp * error_z, self.vertical_limit)

        self.command_publisher.publish(command)


def main(args=None):
    rclpy.init(args=args)
    node = PositionController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

"""Check command direction, speed limits, stale-input stop, and recovery."""
import time
import unittest

import rclpy
from rclpy.executors import SingleThreadedExecutor
from geometry_msgs.msg import PoseStamped
from crazyflie_interfaces.msg import FullState
from capstone_demo.controller import PositionController


class ControllerTest(unittest.TestCase):
    def test_feedback_and_timeout(self):
        rclpy.init()
        controller = PositionController()
        probe = rclpy.create_node('controller_test')
        executor = SingleThreadedExecutor()
        executor.add_node(controller)
        executor.add_node(probe)
        commands = []
        subscription = probe.create_subscription(
            FullState, '/cf1/cmd_full_state', commands.append, 10)
        targets = probe.create_publisher(PoseStamped, '/cf1/desired_state', 10)
        poses = probe.create_publisher(PoseStamped, '/cf1/pose', 10)
        target = PoseStamped()
        target.pose.position.x = 1.0
        target.pose.position.y = -1.0
        target.pose.position.z = 0.5
        target.pose.orientation.w = 1.0
        pose = PoseStamped()
        pose.pose.orientation.w = 1.0

        def run_for(seconds, send_feedback):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                if send_feedback:
                    targets.publish(target)
                    poses.publish(pose)
                executor.spin_once(timeout_sec=0.01)

        try:
            run_for(1.0, True)
            self.assertTrue(commands)
            velocity = commands[-1].twist.linear
            self.assertAlmostEqual(velocity.x, 0.25)
            self.assertAlmostEqual(velocity.y, -0.25)
            self.assertAlmostEqual(velocity.z, 0.30)
            run_for(1.0, False)
            velocity = commands[-1].twist.linear
            self.assertEqual((velocity.x, velocity.y, velocity.z), (0.0, 0.0, 0.0))
            run_for(0.5, True)
            self.assertGreater(commands[-1].twist.linear.x, 0.0)
        finally:
            executor.shutdown()
            controller.destroy_node()
            probe.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    unittest.main()

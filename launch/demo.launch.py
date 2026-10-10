"""Start Gazebo, the planner/controller, the simulator adapter and RViz."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package = get_package_share_directory('capstone_demo')
    gazebo = get_package_share_directory('ros_gz_sim')
    world_package = get_package_share_directory('ros_gz_crazyflie_gazebo')
    world = os.path.join(world_package, 'worlds', 'crazyflie_world.sdf')

    arguments = [
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('gz_args', default_value=world + ' -r'),
        DeclareLaunchArgument('waypoint_file', default_value=os.path.join(package, 'config', 'assignment.yaml')),
        DeclareLaunchArgument('output_dir', default_value='/tmp/capstone-demo'),
        DeclareLaunchArgument('startup_delay', default_value='4.0'),
        DeclareLaunchArgument('kp', default_value='0.9'),
    ]
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': LaunchConfiguration('gz_args')}.items())
    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        parameters=[{'config_file': os.path.join(package, 'config', 'bridge.yaml')}])
    adapter = Node(
        package='capstone_demo', executable='gazebo_adapter',
        parameters=[{'use_sim_time': True}], output='screen')
    controller = Node(
        package='capstone_demo', executable='controller',
        parameters=[{
            'use_sim_time': True,
            'kp': ParameterValue(LaunchConfiguration('kp'), value_type=float)}],
        output='screen')
    planner = Node(
        package='capstone_demo', executable='trajectory_planner',
        parameters=[{
            'use_sim_time': True,
            'waypoint_file': LaunchConfiguration('waypoint_file'),
            'output_dir': LaunchConfiguration('output_dir'),
            'startup_delay': ParameterValue(LaunchConfiguration('startup_delay'), value_type=float)}],
        output='screen')
    rviz = Node(
        package='rviz2', executable='rviz2',
        arguments=['-d', os.path.join(package, 'config', 'demo.rviz')],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')))
    return LaunchDescription(arguments + [simulation, bridge, adapter, controller, planner, rviz])

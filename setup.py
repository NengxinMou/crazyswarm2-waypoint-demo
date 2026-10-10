from glob import glob
from setuptools import setup

package_name = 'capstone_demo'

setup(
    name=package_name,
    version='0.2.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/config', glob('config/*')),
    ],
    install_requires=['setuptools'],
    description='Simple waypoint flight with a P position controller in Gazebo',
    entry_points={
        'console_scripts': [
            'trajectory_planner = capstone_demo.trajectory_planner:main',
            'controller = capstone_demo.controller:main',
            'gazebo_adapter = capstone_demo.gazebo_adapter:main',
        ],
    },
)

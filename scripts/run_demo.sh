#!/usr/bin/env bash
set -e
package_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
workspace_dir=$(cd -- "$package_dir/../.." && pwd)
source /opt/ros/humble/setup.bash
source "$workspace_dir/install/local_setup.bash"
model_dir=${CF_SIM_MODEL_DIR:-"$workspace_dir/../simulation_ws/crazyflie-simulation/simulator_files/gazebo"}
if [[ ! -f "$model_dir/crazyflie/model.sdf" ]]; then
    echo "Model not found. Set CF_SIM_MODEL_DIR to the simulator_files/gazebo directory."
    exit 1
fi
export GZ_SIM_RESOURCE_PATH="$model_dir${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-96}
export ROS_LOCALHOST_ONLY=1
export GZ_PARTITION=${GZ_PARTITION:-capstone_demo_live}
output_dir=${DEMO_OUTPUT_DIR:-"$package_dir/results/latest"}
echo 'Demo: take off to 1 m, fly 1 m along +y, and land.'
echo 'Cyan: measured path. Orange: planned path. Ctrl+C to stop.'
exec ros2 launch capstone_demo demo.launch.py output_dir:="$output_dir" "$@"

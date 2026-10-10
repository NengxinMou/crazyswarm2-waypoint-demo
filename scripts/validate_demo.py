"""Run the waypoint examples without GUI and check the measured results."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time

package = Path(__file__).resolve().parents[1]
workspace = package.parents[1]
world = workspace / 'install/ros_gz_crazyflie_gazebo/share/ros_gz_crazyflie_gazebo/worlds/crazyflie_world.sdf'

for number, example in enumerate(['assignment', 'square']):
    output = package / 'results' / ('test-' + example)
    output.mkdir(parents=True, exist_ok=True)
    report = output / 'result.json'
    if report.exists():
        report.unlink()
    environment = dict(os.environ, ROS_DOMAIN_ID=str(101 + number),
                       GZ_PARTITION='capstone_test_' + example,
                       DEMO_OUTPUT_DIR=str(output))
    command = ['bash', str(package / 'scripts/run_demo.sh'), 'rviz:=false',
               'gz_args:=' + str(world) + ' -s -r',
               'waypoint_file:=' + str(package / 'config' / (example + '.yaml'))]
    with (output / 'simulation.log').open('w') as log:
        process = subprocess.Popen(command, env=environment, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                if report.exists():
                    result = json.loads(report.read_text())
                    assert result['passed'], result
                    expected_count = 3 if example == 'assignment' else 6
                    assert len(result['stages']) == expected_count, result
                    errors = [stage['error_m'] for stage in result['stages']]
                    assert max(errors) < 0.07, result
                    print(f'{example}: PASS, {expected_count} waypoints, max arrival error {max(errors):.4f} m', flush=True)
                    break
                if process.poll() is not None:
                    raise RuntimeError(f'{example} launch exited; see {output}')
                time.sleep(0.5)
            else:
                raise RuntimeError(f'{example} timed out; see {output}')
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=10)
    subprocess.run(['python3', str(package / 'scripts/plot_flight.py'),
                    str(output / 'flight.csv')], check=True)

"""Plot logged ROS positions; no generated or interpolated flight data."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('flight_csv', type=Path)
args = parser.parse_args()
data = np.genfromtxt(args.flight_csv, delimiter=',', names=True, dtype=None, encoding='utf-8')
data = np.atleast_1d(data)
if len(data) < 2:
    raise SystemExit('Need at least two flight samples.')

fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
for axis, name in zip(axes, ['x', 'y', 'z']):
    axis.step(data['time_s'], data['target_' + name], where='post', color='#e58d24', linestyle='--', label='Target')
    axis.plot(data['time_s'], data['actual_' + name], color='#087e8b', label='Measured')
    axis.set_ylabel(name + ' (m)')
    axis.grid(alpha=0.25)
    if np.ptp(data['target_' + name]) < 0.01:
        centre = float(data['target_' + name][0])
        axis.set_ylim(centre - 0.05, centre + 0.05)
axes[0].set_title('Gazebo waypoint flight - P position control')
axes[0].legend(loc='upper right')
axes[-1].set_xlabel('Simulation time since startup (s)')
fig.tight_layout()
fig.savefig(args.flight_csv.with_name('position_tracking.png'), dpi=180)
plt.close(fig)

fig = plt.figure(figsize=(8, 6))
axis = fig.add_subplot(111, projection='3d')
axis.plot(data['actual_x'], data['actual_y'], data['actual_z'], color='#087e8b', label='Measured flight')
# Extract each distinct waypoint from the recorded targets.
targets = [(0.0, 0.0, 0.0)]
for row in data:
    target = (row['target_x'], row['target_y'], row['target_z'])
    if target != targets[-1]:
        targets.append(target)
points = np.array(targets)
axis.plot(points[:, 0], points[:, 1], points[:, 2], 'o--', color='#e58d24', label='Planned waypoints')
axis.set_xlabel('x (m)')
axis.set_ylabel('y (m)')
axis.set_zlabel('z (m)')
axis.set_title('Measured flight path in Gazebo')
axis.legend()
fig.tight_layout()
fig.savefig(args.flight_csv.with_name('flight_path.png'), dpi=180)
print('Saved position_tracking.png and flight_path.png')

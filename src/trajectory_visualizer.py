"""Kinematic Trajectory Visualizer and Heatmapper for AI Computer Interaction Logger.

Performs behavioral kinematics analysis, plotting 2D Gaussian click heatmaps,
velocity vector gradients, speed/acceleration profiles, and compiling beautiful,
standalone diagnostic HTML analytics dashboards with embedded SVG vector graphics.
"""

import os
import math
import csv
import json
from typing import List, Tuple, Dict, Any, Optional
import cv2
import numpy as np


class TrajectoryVisualizer:
    """Enterprise kinematics analyzer generating graphical mouse velocity heatmaps and HTML reports."""

    def __init__(self, output_report_dir: str = "reports"):
        """Initialize the kinematics analyzer and setup directory structure."""
        self.output_report_dir = output_report_dir
        os.makedirs(self.output_report_dir, exist_ok=True)

    def compute_gaussian_kernel(self, radius: int, sigma: float) -> np.ndarray:
        """Generate a 2D Gaussian weight matrix to represent mouse click landing dispersion."""
        size = 2 * radius + 1
        x, y = np.mgrid[-radius:radius+1, -radius:radius+1]
        g = np.exp(-(x**2 + y**2) / (2.0 * sigma**2))
        return g / g.max()

    def generate_click_heatmap(self, base_image_path: str, clicks: List[Tuple[int, int]], output_path: str, radius: int = 40, sigma: float = 15.0) -> None:
        """Generate a glowing translucent thermal click landing heatmap over a screenshot image.
        
        Applies mathematical Gaussian overlays and translates weights into smooth RGB color spectrums.
        """
        if not os.path.exists(base_image_path):
            return

        img = cv2.imread(base_image_path)
        if img is None:
            return

        h, w, _ = img.shape
        heatmap_accum = np.zeros((h, w), dtype=np.float32)
        g_kernel = self.compute_gaussian_kernel(radius, sigma)

        for (cx, cy) in clicks:
            # Bound check coordinates
            if not (0 <= cx < w and 0 <= cy < h):
                continue

            # Crop kernel bounds near borders
            x_start = max(0, cx - radius)
            x_end = min(w, cx + radius + 1)
            y_start = max(0, cy - radius)
            y_end = min(h, cy + radius + 1)

            k_x_start = x_start - (cx - radius)
            k_x_end = k_x_start + (x_end - x_start)
            k_y_start = y_start - (cy - radius)
            k_y_end = k_y_start + (y_end - y_start)

            # Accumulate landing intensities
            heatmap_accum[y_start:y_end, x_start:x_end] += g_kernel[k_y_start:k_y_end, k_x_start:k_x_end]

        # Normalize accumulative values
        if heatmap_accum.max() > 0:
            heatmap_accum = heatmap_accum / heatmap_accum.max()

        # Apply a jet thermal color map to translated weights
        heatmap_gray = np.uint8(255 * heatmap_accum)
        heatmap_color = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_JET)

        # Translucent overlay onto original screenshot
        alpha = 0.55
        overlay_img = cv2.addWeighted(heatmap_color, alpha, img, 1 - alpha, 0)
        cv2.imwrite(output_path, overlay_img)

    def draw_velocity_vector_paths(self, base_image_path: str, path_coords: List[Tuple[int, int]], output_path: str) -> None:
        """Trace continuous mouse path vectors with colored acceleration gradients (cool cyan to hot magenta)."""
        if not os.path.exists(base_image_path) or len(path_coords) < 2:
            return

        img = cv2.imread(base_image_path)
        if img is None:
            return

        # Draw lines between sequential positions
        for i in range(len(path_coords) - 1):
            x1, y1 = path_coords[i]
            x2, y2 = path_coords[i+1]

            # Compute pixel distance as a basic proxy for acceleration speed
            dist = math.hypot(x2 - x1, y2 - y1)
            
            # Line transitions to magenta at high speed speeds
            ratio = min(1.0, dist / 80.0)
            color_b = int(255 * (1.0 - ratio))  # High cyan weight at low speed
            color_g = int(220 * (1.0 - ratio))
            color_r = int(255 * ratio)          # High magenta weight at high speed

            cv2.line(img, (x1, y1), (x2, y2), (color_b, color_g, color_r), 3)
            # Arrow head pointing to direction
            if i % 3 == 0:
                cv2.circle(img, (x2, y2), 4, (color_b, color_g, color_r), -1)

        cv2.imwrite(output_path, img)

    def analyze_session_kinematics(self, session_dir: str) -> Dict[str, Any]:
        """Compute speed, acceleration, and jerk profiles across mouse movements."""
        events_csv = os.path.join(session_dir, "events.csv")
        metrics = {
            "total_distance_px": 0.0,
            "average_speed_px_sec": 0.0,
            "max_acceleration": 0.0,
            "jerk_score": 0.0,
            "coordinates_count": 0,
            "anomalies_flagged": 0,
            "movement_type": "Human (Organic)"
        }

        if not os.path.exists(events_csv):
            return metrics

        coordinates: List[Tuple[float, int, int]] = []
        
        # Load mouse events with timestamp values
        with open(events_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                next(reader)
            except StopIteration:
                return metrics

            for row in reader:
                if len(row) < 3:
                    continue
                ts = float(row[0])
                event_type = row[1]
                data = row[2]

                if "mouse_move" in event_type or "mouse_click" in event_type:
                    # Parse x, y coordinates
                    match = re.search(r'x=(\d+),\s*y=(\d+)', data)
                    if match:
                        x, y = int(match.group(1)), int(match.group(2))
                        coordinates.append((ts, x, y))

        if len(coordinates) < 3:
            return metrics

        metrics["coordinates_count"] = len(coordinates)
        speeds: List[float] = []
        accelerations: List[float] = []
        jerks: List[float] = []

        for i in range(len(coordinates) - 1):
            t1, x1, y1 = coordinates[i]
            t2, x2, y2 = coordinates[i+1]

            dt = t2 - t1
            if dt <= 0:
                dt = 0.001

            dist = math.hypot(x2 - x1, y2 - y1)
            metrics["total_distance_px"] += dist

            speed = dist / dt
            speeds.append(speed)

        for i in range(len(speeds) - 1):
            dt = coordinates[i+2][0] - coordinates[i+1][0]
            if dt <= 0:
                dt = 0.001

            accel = (speeds[i+1] - speeds[i]) / dt
            accelerations.append(accel)

        for i in range(len(accelerations) - 1):
            dt = coordinates[i+3][0] - coordinates[i+2][0]
            if dt <= 0:
                dt = 0.001

            jerk = (accelerations[i+1] - accelerations[i]) / dt
            jerks.append(jerk)

        # Statistical aggregates
        if speeds:
            metrics["average_speed_px_sec"] = sum(speeds) / len(speeds)
        if accelerations:
            metrics["max_acceleration"] = max([abs(a) for a in accelerations])
        if jerks:
            metrics["jerk_score"] = sum([abs(j) for j in jerks]) / len(jerks)

        # Flag anomalies (e.g. perfectly straight lines with zero speed variance indicator of bot activity)
        speed_variance = np.var(speeds) if len(speeds) > 1 else 0
        if speed_variance < 10.0 and metrics["total_distance_px"] > 200:
            metrics["movement_type"] = "Bot (Synthetic/Linear)"
            metrics["anomalies_flagged"] += 1

        return metrics

    def compile_html_report(self, session_id: str, metrics: Dict[str, Any], path_svg_points: List[Tuple[int, int]]) -> str:
        """Compile a beautiful standalone HTML report showcasing interactive SVG coordinate paths and tables."""
        output_file = os.path.join(self.output_report_dir, f"report_{session_id}.html")

        # Construct beautiful responsive SVG line vectors representing mouse trajectories
        svg_lines = ""
        if path_svg_points:
            svg_lines = f'<polyline points="{" ".join([f"{x},{y}" for x, y in path_svg_points])}" fill="none" stroke="#22d3ee" stroke-width="3" />'
            for (x, y) in path_svg_points[::4]:
                svg_lines += f'<circle cx="{x}" cy="{y}" r="4" fill="#f43f5e" />'

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Behavioral Trajectory Diagnostic Report - {session_id}</title>
    <style>
        body {{
            background: #0f172a;
            color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: #1e293b;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
            border: 1px solid #475569;
        }}
        h1 {{
            color: #22d3ee;
            border-bottom: 2px solid #334155;
            padding-bottom: 12px;
            margin-top: 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #334155;
        }}
        th {{
            background: #334155;
            color: #22d3ee;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-green {{
            background: #064e3b;
            color: #34d399;
        }}
        .badge-red {{
            background: #7f1d1d;
            color: #f87171;
        }}
        .canvas-container {{
            background: #0b0f19;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #475569;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Behavioral Trajectory Report</h1>
        <p><strong>Session ID:</strong> {session_id}</p>
        
        <div class="grid">
            <div>
                <h3>Kinematic Metrics</h3>
                <table>
                    <tr>
                        <th>Parameter</th>
                        <th>Measured Value</th>
                    </tr>
                    <tr>
                        <td>Total Distance Traveled</td>
                        <td>{metrics["total_distance_px"]:.2f} pixels</td>
                    </tr>
                    <tr>
                        <td>Average Interaction Speed</td>
                        <td>{metrics["average_speed_px_sec"]:.2f} px/sec</td>
                    </tr>
                    <tr>
                        <td>Peak Velocity Acceleration</td>
                        <td>{metrics["max_acceleration"]:.2f} px/sec²</td>
                    </tr>
                    <tr>
                        <td>Relative Jerk Friction Index</td>
                        <td>{metrics["jerk_score"]:.2f} px/sec³</td>
                    </tr>
                    <tr>
                        <td>Coordinate Steps Recorded</td>
                        <td>{metrics["coordinates_count"]} frames</td>
                    </tr>
                    <tr>
                        <td>Behavioral Classification</td>
                        <td>
                            <span class="badge {"badge-green" if "Human" in metrics["movement_type"] else "badge-red"}">
                                {metrics["movement_type"]}
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div>
                <h3>Trajectory Plot (SVG Render)</h3>
                <div class="canvas-container">
                    <svg width="450" height="300" viewBox="0 0 1920 1080" style="background: #020617; border-radius: 8px;">
                        {svg_lines}
                    </svg>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_file
import re

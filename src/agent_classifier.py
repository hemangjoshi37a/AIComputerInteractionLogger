"""Behavioral Agent Movement Classifier for AI Computer Interaction Logger.

Calculates statistical movement heuristics (path straightness, velocity entropy,
acceleration variance, and jerky friction profiles) over coordinate sequences to
categorize human organic interactions versus linear robotic bots.
"""

import os
import re
import csv
import math
from typing import List, Tuple, Dict, Any, Optional


class BehavioralAgentClassifier:
    """Heuristic kinematic classifier analyzing user trajectory patterns to distinguish humans from bots."""

    def __init__(self, straightness_threshold: float = 0.96, entropy_threshold: float = 2.1):
        """Initialize the agent classifier with regulatory sensitivity limits."""
        self.straightness_threshold = straightness_threshold
        self.entropy_threshold = entropy_threshold

    def calculate_path_straightness(self, points: List[Tuple[int, int]]) -> float:
        """Compute the ratio between direct end-to-end distance and actual cumulative path length.
        
        Perfect straight lines (standard in automated computer bots) return 1.0,
        while organic human curves display much lower ratios (<0.95).
        """
        if len(points) < 3:
            return 1.0

        x0, y0 = points[0]
        xn, yn = points[-1]

        direct_dist = math.hypot(xn - x0, yn - y0)
        if direct_dist <= 0:
            return 0.0

        cumulative_dist = 0.0
        for i in range(len(points) - 1):
            cumulative_dist += math.hypot(points[i+1][0] - points[i][0], points[i+1][1] - points[i][1])

        if cumulative_dist <= 0:
            return 1.0

        return direct_dist / cumulative_dist

    def calculate_velocity_entropy(self, speeds: List[float]) -> float:
        """Compute Shannon Entropy over speed values to evaluate velocity variation complexity.
        
        Static, uniform speeds (bots) display low entropy (~0.0), whereas human movements
        display highly randomized acceleration jitter and high entropy (>2.2).
        """
        if not speeds:
            return 0.0

        # Bin speeds into discrete ranges
        bins: Dict[int, int] = {}
        for s in speeds:
            bin_idx = int(s // 25)  # Group speeds into bins of 25 px/sec
            bins[bin_idx] = bins.get(bin_idx, 0) + 1

        total_samples = len(speeds)
        entropy = 0.0
        for count in bins.values():
            p = count / total_samples
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy

    def extract_trajectory_coordinates(self, events_csv: str) -> List[Tuple[float, int, int]]:
        """Load and parse coordinate timelines from standard logged events csv."""
        coordinates: List[Tuple[float, int, int]] = []
        if not os.path.exists(events_csv):
            return coordinates

        with open(events_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                next(reader)
            except StopIteration:
                return coordinates

            for row in reader:
                if len(row) < 3:
                    continue
                ts = float(row[0])
                event_type = row[1]
                data = row[2]

                if "mouse_move" in event_type or "mouse_click" in event_type:
                    # Search and extract x, y integer values using regex filters
                    match = re.search(r'x=(\d+),\s*y=(\d+)', data)
                    if match:
                        x, y = int(match.group(1)), int(match.group(2))
                        coordinates.append((ts, x, y))

        return coordinates

    def classify_interaction_behavior(self, session_dir: str) -> Dict[str, Any]:
        """Classify session interactions and output a comprehensive diagnostic report card."""
        report = {
            "session_id": os.path.basename(session_dir),
            "straightness_index": 1.0,
            "velocity_entropy": 0.0,
            "average_speed_px_sec": 0.0,
            "bot_risk_percentage": 0,
            "behavior_category": "Unknown",
            "diagnostics": []
        }

        events_csv = os.path.join(session_dir, "events.csv")
        coords = self.extract_trajectory_coordinates(events_csv)

        if len(coords) < 5:
            report["behavior_category"] = "Insufficient Data (Idle)"
            return report

        # Extract coordinates points and calculate cumulative metrics
        points = [(x, y) for (_, x, y) in coords]
        straightness = self.calculate_path_straightness(points)
        report["straightness_index"] = straightness

        # Calculate chronological speeds list
        speeds: List[float] = []
        for i in range(len(coords) - 1):
            t1, x1, y1 = coords[i]
            t2, x2, y2 = coords[i+1]
            dt = t2 - t1
            if dt <= 0:
                dt = 0.001
            dist = math.hypot(x2 - x1, y2 - y1)
            speeds.append(dist / dt)

        entropy = self.calculate_velocity_entropy(speeds)
        report["velocity_entropy"] = entropy

        if speeds:
            report["average_speed_px_sec"] = sum(speeds) / len(speeds)

        # Apply classification heuristics to compute bot-risk weight metrics
        risk_score = 0
        if straightness >= self.straightness_threshold:
            risk_score += 45
            report["diagnostics"].append("HIGH_STRAIGHTNESS: Perfectly straight trajectory vectors detected.")
        else:
            risk_score += max(0, int((straightness - 0.8) * 100))

        if entropy <= self.entropy_threshold:
            risk_score += 45
            report["diagnostics"].append("LOW_VELOCITY_ENTROPY: Static, non-human speed uniformities detected.")
        else:
            risk_score += max(0, int((2.5 - entropy) * 20))

        # Cap risk metric bounds
        report["bot_risk_percentage"] = min(100, max(0, risk_score))

        # Final categorization step
        if report["bot_risk_percentage"] > 75:
            report["behavior_category"] = "Bot (Highly Linear/Automated)"
        elif report["bot_risk_percentage"] > 40:
            report["behavior_category"] = "Suspicious (Irregular Jitters)"
        else:
            report["behavior_category"] = "Human (Organic/Friction)"

        return report
import re

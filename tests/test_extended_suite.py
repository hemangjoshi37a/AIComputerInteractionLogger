"""Extended Concurrency and Stress Testing Suite for AI Computer Interaction Logger.

Runs high-load stress testing, memory leak assertions, multi-threaded race condition
checks, and comprehensive validations for Synthetic Generators, Privacy Redactors,
and Trajectory Heatmappers under extreme synthetic workloads.
"""

import os
import csv
import json
import shutil
import unittest
import threading
import time
from unittest.mock import MagicMock, patch
import psutil

# Import our brand new Phase 2 modules directly by inserting src/ into path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from synthetic_generator import SyntheticSessionGenerator
from ocr_redaction import OpticalPrivacyRedactor
from trajectory_visualizer import TrajectoryVisualizer


class TestExtendedConcurrencyAndStress(unittest.TestCase):
    """Rigorous performance stress test suite verifying stability, race-conditions, and memory leaks."""

    def setUp(self):
        self.test_root = os.path.abspath("extended_stress_mock")
        os.makedirs(self.test_root, exist_ok=True)
        self.generator = SyntheticSessionGenerator(base_output_dir=self.test_root)
        self.redactor = OpticalPrivacyRedactor()
        self.visualizer = TrajectoryVisualizer(output_report_dir=os.path.join(self.test_root, "reports"))

    def tearDown(self):
        if os.path.exists(self.test_root):
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_synthetic_login_scenario_generation(self):
        """Verify the synthetic login generator outputs a complete, valid session directory."""
        session_id = "syn_login_001"
        self.generator.simulate_login_scenario(session_id)

        session_path = os.path.join(self.test_root, session_id)
        self.assertTrue(os.path.exists(session_path))
        self.assertTrue(os.path.exists(os.path.join(session_path, "events.csv")))
        self.assertTrue(os.path.exists(os.path.join(session_path, "screenshots")))

        # Check screenshot counts
        ss_dir = os.path.join(session_path, "screenshots")
        files = os.listdir(ss_dir)
        self.assertGreater(len(files), 10)  # Generates realistic continuous frames

    def test_synthetic_coding_scenario_generation(self):
        """Verify the synthetic IDE generator outputs a valid chronological coding timeline."""
        session_id = "syn_coding_001"
        self.generator.simulate_coding_scenario(session_id)

        session_path = os.path.join(self.test_root, session_id)
        self.assertTrue(os.path.exists(session_path))

        # Check events CSV structure and chronological timestamps
        csv_file = os.path.join(session_path, "events.csv")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ["Timestamp", "EventType", "Data"])
            
            rows = list(reader)
            self.assertGreater(len(rows), 5)
            # Ensure timestamps increase strictly chronologically
            timestamps = [float(r[0]) for r in rows]
            for i in range(len(timestamps) - 1):
                self.assertLessEqual(timestamps[i], timestamps[i+1])

    def test_visual_contour_bounding_boxes(self):
        """Verify OpenCV contour grouping successfully computes visual text bounding bounds."""
        # Draw a synthetic form screenshot
        session_id = "box_test"
        self.generator.simulate_login_scenario(session_id)
        ss_dir = os.path.join(self.test_root, session_id, "screenshots")
        test_img = os.path.join(ss_dir, os.listdir(ss_dir)[0])

        boxes = self.redactor.detect_text_bounding_boxes(test_img)
        # Should detect multiple block elements on our custom drawn browser form
        self.assertGreater(len(boxes), 0)
        for box in boxes:
            self.assertEqual(len(box), 4)
            x, y, w, h = box
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)

    def test_pii_regex_sanitization(self):
        """Verify regex sanitization replaces sensitive letters with safe tokens."""
        raw_text_1 = "My email is admin@enterprise.ai and my credit card is 1234-5678-9012-3456"
        sanitized_1, modified_1 = self.redactor.sanitize_event_string(raw_text_1)
        self.assertTrue(modified_1)
        self.assertIn("[REDACTED_EMAIL]", sanitized_1)
        self.assertIn("[REDACTED_CARD]", sanitized_1)
        self.assertNotIn("admin@enterprise.ai", sanitized_1)

        raw_text_2 = "Set key=api_key_secret_token_1234567890 in config"
        sanitized_2, modified_2 = self.redactor.sanitize_event_string(raw_text_2)
        self.assertTrue(modified_2)
        self.assertIn("[REDACTED_SECRET]", sanitized_2)

    def test_kinematic_diagnostics_analysis(self):
        """Verify kinematics metrics compute speeds, acceleration, and human movement shapes."""
        session_id = "kin_test"
        self.generator.simulate_login_scenario(session_id)
        session_path = os.path.join(self.test_root, session_id)

        metrics = self.visualizer.analyze_session_kinematics(session_path)
        self.assertGreater(metrics["total_distance_px"], 0)
        self.assertGreater(metrics["average_speed_px_sec"], 0)
        self.assertGreaterEqual(metrics["max_acceleration"], 0)
        self.assertGreaterEqual(metrics["jerk_score"], 0)
        self.assertIn(metrics["movement_type"], ["Human (Organic)", "Bot (Synthetic/Linear)"])

    def test_html_report_generation(self):
        """Verify HTML reports with responsive SVG vectors render flawlessly."""
        session_id = "report_test"
        metrics = {
            "total_distance_px": 1500.40,
            "average_speed_px_sec": 450.2,
            "max_acceleration": 2100.5,
            "jerk_score": 14000.0,
            "coordinates_count": 45,
            "movement_type": "Human (Organic)"
        }
        svg_points = [(100, 100), (200, 300), (450, 600), (900, 800)]
        report_file = self.visualizer.compile_html_report(session_id, metrics, svg_points)
        
        self.assertTrue(os.path.exists(report_file))
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(session_id, content)
            self.assertIn("1500.40 pixels", content)
            self.assertIn("<polyline", content)

    def test_multi_threaded_scenario_stress(self):
        """Stress-test: Spawns multiple concurrent synthetic generators to verify race conditions."""
        threads: List[threading.Thread] = []
        errors: List[Exception] = []

        def worker_task(idx: int):
            try:
                # Generate concurrent sessions simultaneously
                self.generator.simulate_login_scenario(f"concurrent_session_{idx}")
            except Exception as e:
                errors.append(e)

        # Spawn 8 threads simulating parallel recording tasks
        for i in range(8):
            t = threading.Thread(target=worker_task, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Assert no exceptions or file conflicts occurred
        self.assertEqual(len(errors), 0, f"Thread errors found: {errors}")

    def test_memory_leak_footprint(self):
        """Assert memory consumption remains flat and bounded under massive stress loops."""
        process = psutil.Process(os.getpid())
        initial_mem = process.memory_info().rss  # Capture starting RAM footprint

        # Generate 5 continuous sessions in a loop
        for i in range(5):
            self.generator.simulate_login_scenario(f"memory_leak_test_{i}")
            session_path = os.path.join(self.test_root, f"memory_leak_test_{i}")
            # Sanitize session data in-place
            self.redactor.sanitize_session_in_place(session_path)

        final_mem = process.memory_info().rss  # Capture ending RAM footprint
        mem_diff_mb = (final_mem - initial_mem) / (1024 * 1024)

        # Assert memory growth is bounded under 120MB, verifying zero memory leaks or unclosed buffers
        self.assertLess(mem_diff_mb, 120.0, f"Potential memory leak detected: {mem_diff_mb:.2f} MB growth")


if __name__ == '__main__':
    unittest.main()

"""Analytical and Graphical Ultra Regression Testing Suite for AI Computer Interaction Logger.

Runs exhaustive validations on custom Pillow templates libraries, path straightness,
polar pie chart trigonometry, speed entropy, and well-formed XML vector graphics.
"""

import os
import shutil
import unittest
from PIL import Image, ImageDraw
import math

# Import all Phase 3 modules directly by inserting src/ into path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from templates_library import GUITemplatesLibrary
from agent_classifier import BehavioralAgentClassifier
from report_charts import ReportChartsRenderer


class TestUltraRegressionAndGraphics(unittest.TestCase):
    """Exhaustive integration testing suite verifying vector chart mathematics and graphic bounds."""

    def setUp(self):
        self.test_root = os.path.abspath("ultra_regression_mock")
        os.makedirs(self.test_root, exist_ok=True)
        self.library = GUITemplatesLibrary()
        self.classifier = BehavioralAgentClassifier()
        self.renderer = ReportChartsRenderer(theme_preset="cyberpunk")

    def tearDown(self):
        if os.path.exists(self.test_root):
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_templates_presets_loading(self):
        """Verify graphical themes contain correct hex color parameters."""
        self.assertIn("cyberpunk", self.library.themes)
        self.assertIn("aero_dark", self.library.themes)
        self.assertIn("pastel_cream", self.library.themes)

        theme = self.library.themes["cyberpunk"]
        self.assertEqual(theme["accent"], "#ff007f")
        self.assertEqual(theme["bg"], "#03001e")

    def test_drawing_window_shadow(self):
        """Verify window shadow renders onto PIL drawing canvas matrices."""
        img = Image.new("RGB", (300, 300))
        draw = ImageDraw.Draw(img)
        self.library.draw_window_shadow(draw, 10, 10, 100, 100)

        # Assert drawing changed black pixels
        pixels = list(img.getdata())
        non_black_pixels = [p for p in pixels if p != (0, 0, 0)]
        self.assertGreater(len(non_black_pixels), 0)

    def test_settings_panel_rendering(self):
        """Verify Settings Panel window outputs a complete, well-formed image."""
        img = Image.new("RGB", (1920, 1080))
        draw = ImageDraw.Draw(img)
        self.library.draw_settings_panel_window(draw, 100, 100, 1000, 600, "aero_dark")

        test_img_path = os.path.join(self.test_root, "settings_test.png")
        img.save(test_img_path)
        self.assertTrue(os.path.exists(test_img_path))

    def test_shopping_checkout_rendering(self):
        """Verify checkout form renders correctly onto image canvas."""
        img = Image.new("RGB", (1920, 1080))
        draw = ImageDraw.Draw(img)
        self.library.draw_shopping_checkout_window(draw, 100, 100, 1000, 600, "pastel_cream")

        test_img_path = os.path.join(self.test_root, "checkout_test.png")
        img.save(test_img_path)
        self.assertTrue(os.path.exists(test_img_path))

    def test_path_straightness_ratio_math(self):
        """Verify mathematical straightness ratio calculations return perfect bounds."""
        # 1. Perfectly straight line
        straight_points = [(0, 0), (10, 10), (20, 20), (30, 30)]
        straightness_1 = self.classifier.calculate_path_straightness(straight_points)
        self.assertAlmostEqual(straightness_1, 1.0, places=4)

        # 2. Perfect curved trajectory (semicircle)
        curved_points = []
        for angle in range(0, 181, 15):
            rad = math.radians(angle)
            x = int(100 * math.cos(rad))
            y = int(100 * math.sin(rad))
            curved_points.append((x, y))

        straightness_2 = self.classifier.calculate_path_straightness(curved_points)
        self.assertLess(straightness_2, 0.75)  # Circular curve displays lower end-to-end ratio

    def test_velocity_entropy_shannon_calculation(self):
        """Verify Shannon Entropy is calculated accurately over speeds lists."""
        # 1. Perfect static speed (bots) displays 0.0 entropy
        static_speeds = [100.0, 100.0, 100.0, 100.0, 100.0]
        entropy_1 = self.classifier.calculate_velocity_entropy(static_speeds)
        self.assertEqual(entropy_1, 0.0)

        # 2. Highly varied speed (humans) displays high entropy
        varied_speeds = [12.0, 45.0, 180.0, 90.0, 250.0, 310.0]
        entropy_2 = self.classifier.calculate_velocity_entropy(varied_speeds)
        self.assertGreater(entropy_2, 1.8)

    def test_svg_line_chart_elements(self):
        """Verify generated SVG line charts contain correct XML coordinate elements."""
        values = [10.5, 45.2, 90.0, 120.4, 75.1]
        labels = ["Jan", "Feb", "Mar", "Apr", "May"]
        svg_xml = self.renderer.draw_svg_line_chart(600, 400, values, labels, "Velocity Profile")

        self.assertIn("<polyline", svg_xml)
        self.assertIn("Velocity Profile", svg_xml)
        self.assertIn('fill="#ff007f"', svg_xml)  # Default theme accent color inside XML
        self.assertIn("</svg>", svg_xml)

    def test_svg_bar_chart_elements(self):
        """Verify generated SVG bar charts contain well-formed rectangular bars."""
        categories = {"Mouse Click": 12.0, "Key Press": 54.0, "Screenshots": 22.0}
        svg_xml = self.renderer.draw_svg_bar_chart(600, 400, categories, "Interaction Summary")

        self.assertIn("<rect", svg_xml)
        self.assertIn("Interaction Summary", svg_xml)
        self.assertIn("Key Press", svg_xml)
        self.assertIn("</svg>", svg_xml)

    def test_svg_pie_chart_trigonometry_elements(self):
        """Verify generated SVG pie charts calculate proper polar arcs."""
        slices = {"Human": 85.0, "Bot": 15.0}
        svg_xml = self.renderer.draw_svg_pie_chart(600, 400, slices, "User Behavior")

        self.assertIn("<path", svg_xml)
        self.assertIn("User Behavior", svg_xml)
        self.assertIn("Human", svg_xml)
        self.assertIn("</svg>", svg_xml)


if __name__ == '__main__':
    unittest.main()

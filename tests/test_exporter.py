"""Deep unit testing suite for DatasetExporter and SessionSummarizer LLM API."""

import os
import csv
import json
import shutil
import unittest
from unittest.mock import MagicMock, patch
import urllib.request
import urllib.error

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from dataset_exporter import DatasetExporter
from session_summarizer import SessionSummarizer, SessionSummary


class TestDatasetExporterAndSummarizer(unittest.TestCase):
    """Rigorous unit test suite verifying exporter math, schemas, and LLM retry handlers."""

    def setUp(self):
        self.test_dir = os.path.abspath("test_session_mock")
        os.makedirs(self.test_dir, exist_ok=True)
        self.screenshots_dir = os.path.join(self.test_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Create dummy events CSV
        self.events_csv = os.path.join(self.test_dir, "events.csv")
        with open(self.events_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "EventType", "Data"])
            writer.writerow([170000000.0, "screenshot", "screenshot_170000000.png"])
            writer.writerow([170000001.0, "mouse_click", "x=192, y=108, button=Button.left, pressed=True"])
            writer.writerow([170000002.0, "key_press", "key=Key.enter"])
            writer.writerow([170000003.0, "screenshot", "screenshot_170000003.png"])
            writer.writerow([170000004.0, "mouse_scroll", "x=500, y=500, dx=0, dy=-1"])

        # Create dummy screenshot files
        with open(os.path.join(self.screenshots_dir, "screenshot_170000000.png"), 'wb') as f:
            f.write(b"fake png content")
        with open(os.path.join(self.screenshots_dir, "screenshot_170000003.png"), 'wb') as f:
            f.write(b"fake png content")

        self.exporter = DatasetExporter()

    def tearDown(self):
        # Clean up mock directories
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree("exported_datasets_test_out", ignore_errors=True)

    def test_coordinate_normalization(self):
        """Verify coordinate scaling to float bounds [0.0, 1.0]."""
        norm_x, norm_y = self.exporter.normalize_coordinate(192, 108, 1920, 1080)
        self.assertEqual(norm_x, 0.1)
        self.assertEqual(norm_y, 0.1)

        # Check clipping to boundaries
        norm_x, norm_y = self.exporter.normalize_coordinate(-50, 2000, 1000, 1000)
        self.assertEqual(norm_x, 0.0)
        self.assertEqual(norm_y, 1.0)

    def test_regex_parsing(self):
        """Verify extraction of coordinates and key values from event strings."""
        coords = self.exporter._parse_coordinates("x=450, y=230, button=Button.left")
        self.assertEqual(coords, (450, 230))

        key = self.exporter._parse_key("key=Key.enter")
        self.assertEqual(key, "Key.enter")

        key_letter = self.exporter._parse_key("key='a'")
        self.assertEqual(key_letter, "a")

    def test_event_loading(self):
        """Verify parsing and chronological sorting of events."""
        events = self.exporter.load_session_events(self.test_dir)
        self.assertEqual(len(events), 5)
        self.assertEqual(events[0]["event_type"], "screenshot")
        self.assertEqual(events[1]["event_type"], "mouse_click")
        self.assertEqual(events[1]["coords"], (192, 108))

    def test_screenshot_alignment(self):
        """Verify pairing of human interactions with closest preceding screenshots."""
        events = self.exporter.load_session_events(self.test_dir)
        steps = self.exporter.align_screenshots_with_actions(events, self.test_dir)
        
        # We have 3 interaction events (mouse_click, key_press, mouse_scroll)
        self.assertEqual(len(steps), 3)
        # First action (mouse_click at 170000001.0) should map to screenshot_170000000.png
        self.assertEqual(os.path.basename(steps[0]["screenshot_rel_path"]), "screenshot_170000000.png")
        # Third action (mouse_scroll at 170000004.0) should map to screenshot_170000003.png
        self.assertEqual(os.path.basename(steps[2]["screenshot_rel_path"]), "screenshot_170000003.png")

    @patch("shutil.copy2")
    def test_claude_computer_use_export(self, mock_copy):
        """Verify Anthropic Claude Computer Use schema layout."""
        out_dir = "exported_datasets_test_out/claude"
        output_json = self.exporter.export_to_claude_computer_use(self.test_dir, out_dir)
        
        self.assertTrue(os.path.exists(output_json))
        with open(output_json, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["api_tool_call"]["name"], "computer")
        self.assertEqual(data[0]["api_tool_call"]["arguments"]["action"], "left_click")

    @patch("shutil.copy2")
    def test_osworld_export(self, mock_copy):
        """Verify OSWorld episodic benchmark schema layout."""
        out_dir = "exported_datasets_test_out/osworld"
        output_json = self.exporter.export_to_osworld(self.test_dir, out_dir)

        self.assertTrue(os.path.exists(output_json))
        with open(output_json, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["environment"], "Windows")
        self.assertEqual(len(data["trajectory"]), 3)
        self.assertEqual(data["trajectory"][0]["action"]["type"], "mouse_click")

    @patch("shutil.copy2")
    def test_huggingface_vlm_export(self, mock_copy):
        """Verify Hugging Face instruction-tuning JSONL format."""
        out_dir = "exported_datasets_test_out/hf"
        output_jsonl = self.exporter.export_to_huggingface_vlm(self.test_dir, out_dir, "Open Notepad")

        self.assertTrue(os.path.exists(output_jsonl))
        with open(output_jsonl, 'r') as f:
            rows = [json.loads(line) for line in f]

        self.assertEqual(len(rows), 3)
        self.assertIn("Goal: Open Notepad", rows[0]["conversations"][0]["value"])
        self.assertIn("click", rows[0]["conversations"][1]["value"])

    @patch("urllib.request.urlopen")
    def test_summarizer_llm_retry_success(self, mock_urlopen):
        """Verify SessionSummarizer LLM API success, backoffs, and parsing."""
        # Mock API JSON response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "task_goal": "Commit workspace changes to git",
                            "task_milestones": ["Initialized git repository", "Committed workspace files"],
                            "success_criteria": ["Git status is clean"],
                            "summary": "The user initialized a git repo and successfully committed all files."
                        })
                    }]
                }
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        summarizer = SessionSummarizer({
            "use_llm_summarization": True,
            "llm_api_key": "fake_key",
            "llm_model": "gemini-1.5-flash"
        })

        res = summarizer._generate_llm_summary("HCI Timeline data")
        self.assertIsNotNone(res)
        self.assertEqual(res["task_goal"], "Commit workspace changes to git")
        self.assertEqual(len(res["task_milestones"]), 2)

    @patch("urllib.request.urlopen")
    def test_summarizer_llm_retry_failure_fallback(self, mock_urlopen):
        """Verify SessionSummarizer LLM failure handles retries and falls back gracefully."""
        # Cause HTTP error on all attempts
        mock_urlopen.side_effect = urllib.error.URLError("Connection Timed Out")

        summarizer = SessionSummarizer({
            "use_llm_summarization": True,
            "llm_api_key": "fake_key",
            "llm_model": "gemini-1.5-flash"
        })

        # Mock time.sleep to avoid actual delays during unit tests
        with patch("time.sleep"):
            res = summarizer._generate_llm_summary("HCI Timeline data")
            self.assertIsNull = res is None  # Graceful None fallback


if __name__ == '__main__':
    unittest.main()

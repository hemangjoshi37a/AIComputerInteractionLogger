"""Standardized dataset exporter for multi-modal AI agent training.

Translates raw mouse, keyboard, and window events with screenshots into:
1. Claude's Computer Use API format
2. OSWorld benchmark trajectories
3. Hugging Face multi-modal instruction-tuning datasets (JSONL format with splits)
"""

import os
import re
import csv
import json
import shutil
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DatasetExporter:
    """Enterprise-grade dataset exporter for GUI interaction recordings."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.output_base = self.config.get("label_output_dir", "exported_datasets")
        os.makedirs(self.output_base, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Safely load configuration yaml if present, otherwise fallback to defaults."""
        if os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logging.error(f"Failed to load yaml config: {e}. Using defaults.")
        return {}

    def _parse_coordinates(self, data_str: str) -> Optional[Tuple[int, int]]:
        """Extract x, y integer coordinates from standard event data strings."""
        try:
            # Matches formats like 'x=100, y=200' or 'x=100, y=200, button=...'
            x_match = re.search(r'x=(\d+)', data_str)
            y_match = re.search(r'y=(\d+)', data_str)
            if x_match and y_match:
                return int(x_match.group(1)), int(y_match.group(1))
        except Exception as e:
            logging.debug(f"Failed to parse coordinates from '{data_str}': {e}")
        return None

    def _parse_key(self, data_str: str) -> Optional[str]:
        """Extract the exact key name from standard keyboard event data strings."""
        try:
            # Matches formats like 'key=Key.enter' or 'key=\'a\''
            match = re.search(r'key=(.+)', data_str)
            if match:
                val = match.group(1).strip()
                if val.startswith("'") and val.endswith("'") and len(val) >= 3:
                    return val[1:-1]
                return val
        except Exception as e:
            logging.debug(f"Failed to parse key from '{data_str}': {e}")
        return None

    def load_session_events(self, session_dir: str) -> List[Dict[str, Any]]:
        """Parse raw CSV events into a structured timeline list."""
        events = []
        events_csv = os.path.join(session_dir, "events.csv")
        if not os.path.exists(events_csv):
            logging.warning(f"Events CSV not found: {events_csv}")
            return events

        import re
        try:
            with open(events_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    timestamp = float(row["Timestamp"])
                    event_type = row["EventType"]
                    data = row["Data"]

                    parsed_event = {
                        "timestamp": timestamp,
                        "event_type": event_type,
                        "raw_data": data,
                        "coords": self._parse_coordinates(data),
                        "key": self._parse_key(data)
                    }
                    events.append(parsed_event)
        except Exception as e:
            logging.error(f"Error reading session events from {events_csv}: {e}")

        events.sort(key=lambda x: x["timestamp"])
        return events

    def get_screenshot_resolution(self, session_dir: str) -> Tuple[int, int]:
        """Inspect the first available screenshot to determine exact screen resolution."""
        screenshots_dir = os.path.join(session_dir, "screenshots")
        if os.path.exists(screenshots_dir):
            files = [f for f in os.listdir(screenshots_dir) if f.endswith(".png")]
            if files:
                first_img_path = os.path.join(screenshots_dir, files[0])
                try:
                    img = cv2.imread(first_img_path)
                    if img is not None:
                        h, w, _ = img.shape
                        return w, h
                except Exception as e:
                    logging.error(f"Failed to read image resolution from {first_img_path}: {e}")
        return 1920, 1080  # Reasonable fallback

    def normalize_coordinate(self, x: int, y: int, screen_width: int, screen_height: int) -> Tuple[float, float]:
        """Normalize absolute screen coordinates to floating-point range [0.0, 1.0]."""
        norm_x = max(0.0, min(1.0, float(x) / max(1, screen_width)))
        norm_y = max(0.0, min(1.0, float(y) / max(1, screen_height)))
        return round(norm_x, 4), round(norm_y, 4)

    def align_screenshots_with_actions(self, events: List[Dict[str, Any]], session_dir: str) -> List[Dict[str, Any]]:
        """Pair each human interaction event with the closest captured screenshot state.

        Ensures each action maps to the most recent screenshot taken BEFORE or AT the action.
        """
        screenshots_dir = os.path.join(session_dir, "screenshots")
        screenshot_events = [e for e in events if e["event_type"] == "screenshot"]
        interaction_events = [e for e in events if e["event_type"] in [
            "mouse_click", "mouse_scroll", "key_press", "window_change"
        ]]

        aligned_steps = []
        if not screenshot_events:
            logging.warning("No screenshot events captured in this session.")
            return aligned_steps

        for act in interaction_events:
            # Find the latest screenshot taken before or very close to this action
            best_screenshot = None
            min_diff = float('inf')
            for ss in screenshot_events:
                diff = act["timestamp"] - ss["timestamp"]
                # screenshot must be captured before or within 0.1s after the action
                if diff >= -0.1:
                    if diff < min_diff:
                        min_diff = diff
                        best_screenshot = ss

            if not best_screenshot:
                # Fallback to the first screenshot if action happens immediately
                best_screenshot = screenshot_events[0]

            img_rel_path = os.path.join("screenshots", best_screenshot["raw_data"])
            aligned_steps.append({
                "timestamp": act["timestamp"],
                "action_event": act,
                "screenshot_rel_path": img_rel_path,
                "screenshot_abs_path": os.path.join(session_dir, img_rel_path)
            })

        return aligned_steps

    def export_to_claude_computer_use(self, session_dir: str, output_dir: str) -> str:
        """Export session to Anthropic Claude 3.5 Computer Use API format."""
        events = self.load_session_events(session_dir)
        w, h = self.get_screenshot_resolution(session_dir)
        steps = self.align_screenshots_with_actions(events, session_dir)

        claude_trajectory = []
        os.makedirs(output_dir, exist_ok=True)

        for i, step in enumerate(steps):
            act = step["action_event"]
            screenshot_name = os.path.basename(step["screenshot_rel_path"])
            dest_screenshot = os.path.join(output_dir, "images", screenshot_name)
            os.makedirs(os.path.dirname(dest_screenshot), exist_ok=True)

            if os.path.exists(step["screenshot_abs_path"]):
                shutil.copy2(step["screenshot_abs_path"], dest_screenshot)

            # Map coordinates to raw pixel coordinates (standard for Anthropic's tool API)
            coords = act["coords"] or (0, 0)
            key = act["key"] or ""

            # Standard Anthropic Computer Use tool schemas
            tool_call = {}
            if act["event_type"] == "mouse_click":
                is_pressed = "pressed=True" in act["raw_data"]
                if is_pressed:
                    btn = "left"
                    if "button=Button.right" in act["raw_data"]:
                        btn = "right"
                    elif "button=Button.middle" in act["raw_data"]:
                        btn = "middle"
                    tool_call = {
                        "action": f"{btn}_click",
                        "coordinate": [coords[0], coords[1]]
                    }
            elif act["event_type"] == "key_press":
                if key.startswith("Key."):
                    # Map special pynput keys to standard tool keys
                    key_name = key.replace("Key.", "")
                    tool_call = {
                        "action": "key",
                        "text": key_name
                    }
                else:
                    tool_call = {
                        "action": "type",
                        "text": key
                    }
            elif act["event_type"] == "mouse_scroll":
                dy = 0
                try:
                    dy_match = re.search(r'dy=(-?\d+)', act["raw_data"])
                    if dy_match:
                        dy = int(dy_match.group(1))
                except:
                    pass
                direction = "down" if dy < 0 else "up"
                tool_call = {
                    "action": f"scroll_{direction}",
                    "coordinate": [coords[0], coords[1]]
                }
            elif act["event_type"] == "window_change":
                tool_call = {
                    "action": "window_focus",
                    "window_title": act["raw_data"]
                }

            if tool_call:
                claude_trajectory.append({
                    "step": i + 1,
                    "timestamp": step["timestamp"],
                    "screenshot": f"images/{screenshot_name}",
                    "screen_resolution": {"width": w, "height": h},
                    "api_tool_call": {
                        "name": "computer",
                        "arguments": tool_call
                    }
                })

        output_json = os.path.join(output_dir, "claude_computer_use.json")
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(claude_trajectory, f, indent=2)

        logging.info(f"Claude Computer Use trajectory exported to: {output_json}")
        return output_json

    def export_to_osworld(self, session_dir: str, output_dir: str) -> str:
        """Export session to OSWorld benchmark episodic task format (normalized coordinates)."""
        events = self.load_session_events(session_dir)
        w, h = self.get_screenshot_resolution(session_dir)
        steps = self.align_screenshots_with_actions(events, session_dir)

        osworld_data = {
            "session_id": os.path.basename(session_dir),
            "environment": "Windows",
            "resolution": f"{w}x{h}",
            "trajectory": []
        }
        os.makedirs(output_dir, exist_ok=True)

        for i, step in enumerate(steps):
            act = step["action_event"]
            screenshot_name = os.path.basename(step["screenshot_rel_path"])
            dest_screenshot = os.path.join(output_dir, "screenshots", screenshot_name)
            os.makedirs(os.path.dirname(dest_screenshot), exist_ok=True)

            if os.path.exists(step["screenshot_abs_path"]):
                shutil.copy2(step["screenshot_abs_path"], dest_screenshot)

            raw_coords = act["coords"] or (0, 0)
            norm_x, norm_y = self.normalize_coordinate(raw_coords[0], raw_coords[1], w, h)

            action_dict = {
                "type": act["event_type"],
                "raw_event": act["raw_data"],
                "normalized_coordinate": [norm_x, norm_y],
                "key_value": act["key"] or ""
            }

            osworld_data["trajectory"].append({
                "step_idx": i,
                "timestamp": step["timestamp"],
                "observation": {
                    "screenshot": f"screenshots/{screenshot_name}",
                    "active_window": act["raw_data"] if act["event_type"] == "window_change" else None
                },
                "action": action_dict
            })

        output_json = os.path.join(output_dir, "osworld_trajectory.json")
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(osworld_data, f, indent=2)

        logging.info(f"OSWorld trajectory exported to: {output_json}")
        return output_json

    def export_to_huggingface_vlm(self, session_dir: str, output_dir: str, goal_instruction: str = "Perform computer task") -> str:
        """Export session to Hugging Face multi-modal instruction-tuning dataset format.

        Generates structured JSONL rows containing high-level goal-instructions
        paired with visual screenshots and structured next-action GPT targets.
        """
        events = self.load_session_events(session_dir)
        w, h = self.get_screenshot_resolution(session_dir)
        steps = self.align_screenshots_with_actions(events, session_dir)

        os.makedirs(output_dir, exist_ok=True)
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        jsonl_rows = []

        for i, step in enumerate(steps):
            act = step["action_event"]
            screenshot_name = os.path.basename(step["screenshot_rel_path"])
            dest_screenshot = os.path.join(images_dir, screenshot_name)

            if os.path.exists(step["screenshot_abs_path"]):
                shutil.copy2(step["screenshot_abs_path"], dest_screenshot)

            raw_coords = act["coords"] or (0, 0)
            norm_x, norm_y = self.normalize_coordinate(raw_coords[0], raw_coords[1], w, h)
            key = act["key"] or ""

            # Action target representation in JSON
            target_action = {}
            if act["event_type"] == "mouse_click":
                target_action = {
                    "action": "click",
                    "coordinate": [norm_x, norm_y],
                    "details": act["raw_data"]
                }
            elif act["event_type"] == "key_press":
                target_action = {
                    "action": "type",
                    "text": key
                }
            elif act["event_type"] == "mouse_scroll":
                target_action = {
                    "action": "scroll",
                    "coordinate": [norm_x, norm_y],
                    "details": act["raw_data"]
                }
            elif act["event_type"] == "window_change":
                target_action = {
                    "action": "focus_window",
                    "title": act["raw_data"]
                }

            # Standard Hugging Face multi-modal conversation layout
            conversation = [
                {
                    "from": "human",
                    "value": f"<image>\nGoal: {goal_instruction}\nWhat is the next interactive step?"
                },
                {
                    "from": "gpt",
                    "value": f"```json\n{json.dumps(target_action)}\n```"
                }
            ]

            jsonl_rows.append({
                "id": f"{os.path.basename(session_dir)}_step_{i}",
                "image": f"images/{screenshot_name}",
                "conversations": conversation,
                "metadata": {
                    "timestamp": step["timestamp"],
                    "screen_resolution": {"width": w, "height": h}
                }
            })

        output_jsonl = os.path.join(output_dir, "huggingface_dataset.jsonl")
        with open(output_jsonl, 'w', encoding='utf-8') as f:
            for row in jsonl_rows:
                f.write(json.dumps(row) + "\n")

        logging.info(f"Hugging Face VLM dataset exported to: {output_jsonl}")
        return output_jsonl

    def build_dataset_splits(self, base_sessions_dir: str, train_ratio: float = 0.8, val_ratio: float = 0.1) -> Dict[str, List[str]]:
        """Split recorded sessions into train, validation, and test subsets."""
        sessions = [
            d for d in os.listdir(base_sessions_dir)
            if os.path.isdir(os.path.join(base_sessions_dir, d)) and d.startswith("session_")
        ]
        # Seed for reproducible splits
        np.random.seed(42)
        shuffled = np.random.permutation(sessions)

        n = len(shuffled)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        splits = {
            "train": list(shuffled[:n_train]),
            "val": list(shuffled[n_train:n_train+n_val]),
            "test": list(shuffled[n_train+n_val:])
        }

        logging.info(f"Dataset splits built: Train={len(splits['train'])}, Val={len(splits['val'])}, Test={len(splits['test'])}")
        return splits


if __name__ == "__main__":
    # Self-test/dry-run block
    exporter = DatasetExporter()
    print("Dataset Exporter module compiled successfully.")

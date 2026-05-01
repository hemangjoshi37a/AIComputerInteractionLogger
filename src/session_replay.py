import os
import csv
import time
import logging
import json
import cv2
import numpy as np
from PIL import Image, ImageTk


class SessionReplay:
    """Replays recorded sessions with visual playback."""

    def __init__(self, session_dir, config=None):
        self.session_dir = session_dir
        self.config = config or {}
        self.events = []
        self.screenshots = {}
        self.current_index = 0
        self.playback_speed = self.config.get('playback_speed', 1.0)
        self.is_playing = False
        self.start_time = None
        self.end_time = None

    def load_session(self):
        """Load session data from CSV and screenshots."""
        events_file = os.path.join(self.session_dir, 'events.csv')
        screenshots_dir = os.path.join(self.session_dir, 'screenshots')

        if not os.path.exists(events_file):
            raise FileNotFoundError(f"Events file not found: {events_file}")

        # Load events
        with open(events_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                event = {
                    'timestamp': float(row['Timestamp']),
                    'event_type': row['EventType'],
                    'data': row['Data']
                }
                self.events.append(event)

        # Sort events by timestamp
        self.events.sort(key=lambda x: x['timestamp'])

        if self.events:
            self.start_time = self.events[0]['timestamp']
            self.end_time = self.events[-1]['timestamp']
            logging.info(f"Loaded {len(self.events)} events from {self.start_time} to {self.end_time}")

        # Load screenshots
        if os.path.exists(screenshots_dir):
            for filename in os.listdir(screenshots_dir):
                if filename.endswith('.png'):
                    timestamp = int(filename.replace('screenshot_', '').replace('.png', ''))
                    img_path = os.path.join(screenshots_dir, filename)
                    self.screenshots[timestamp] = img_path
            logging.info(f"Loaded {len(self.screenshots)} screenshots")

    def get_screenshot(self, timestamp):
        """Get screenshot closest to timestamp."""
        if not self.screenshots:
            return None

        closest_timestamp = min(self.screenshots.keys(), key=lambda x: abs(x - timestamp))
        img_path = self.screenshots[closest_timestamp]

        try:
            img = cv2.imread(img_path)
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logging.error(f"Error loading screenshot {img_path}: {e}")
            return None

    def get_events_in_range(self, start_time, end_time):
        """Get events within time range."""
        return [e for e in self.events if start_time <= e['timestamp'] <= end_time]

    def get_events_at_time(self, timestamp, window_seconds=0.5):
        """Get events around a specific timestamp."""
        return self.get_events_in_range(timestamp - window_seconds, timestamp + window_seconds)

    def get_duration(self):
        """Get session duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def get_event_count(self):
        """Get total number of events."""
        return len(self.events)

    def get_screenshot_count(self):
        """Get total number of screenshots."""
        return len(self.screenshots)

    def get_event_types(self):
        """Get unique event types in the session."""
        return list(set(e['event_type'] for e in self.events))

    def get_window_changes(self):
        """Get all window change events."""
        return [e for e in self.events if e['event_type'] == 'window_change']

    def get_mouse_events(self):
        """Get all mouse events."""
        return [e for e in self.events if e['event_type'].startswith('mouse_')]

    def get_keyboard_events(self):
        """Get all keyboard events."""
        return [e for e in self.events if e['event_type'].startswith('key_')]

    def get_summary(self):
        """Get session summary."""
        return {
            'duration': self.get_duration(),
            'event_count': self.get_event_count(),
            'screenshot_count': self.get_screenshot_count(),
            'event_types': self.get_event_types(),
            'window_changes': len(self.get_window_changes()),
            'mouse_events': len(self.get_mouse_events()),
            'keyboard_events': len(self.get_keyboard_events())
        }

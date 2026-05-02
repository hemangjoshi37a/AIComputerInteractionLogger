"""Automated dataset labeling and categorization for recorded sessions."""

import os
import json
import logging
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import re

import numpy as np


@dataclass
class SessionLabel:
    """Represents a label for a session."""
    label_name: str
    confidence: float
    category: str
    description: str


@dataclass
class ActivityTag:
    """Represents an activity detected in a session."""
    tag_name: str
    start_time: float
    end_time: float
    duration: float
    confidence: float
    context: Dict[str, Any]


@dataclass
class LabeledDataset:
    """Complete labeled dataset for a session."""
    session_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    primary_category: str
    categories: List[Dict[str, Any]]
    activity_tags: List[Dict[str, Any]]
    application_usage: Dict[str, Any]
    interaction_patterns: Dict[str, Any]
    ml_features: Dict[str, Any]
    metadata: Dict[str, Any]


class DatasetLabeler:
    """Automatically labels and categorizes recorded sessions."""

    def __init__(self, config=None):
        self.config = config or {}
        self.enabled = self.config.get('labeling_enabled', True)
        self.output_dir = self.config.get('label_output_dir', 'labeled_datasets')
        self.use_ml_classification = self.config.get('use_ml_classification', False)
        self.ml_model_path = self.config.get('ml_model_path', None)

        # Category definitions
        self.categories = self._load_categories()

        # Activity patterns
        self.activity_patterns = self._load_activity_patterns()

        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)

    def _load_categories(self) -> Dict[str, Dict]:
        """Load application and activity category definitions."""
        return {
            'coding': {
                'keywords': ['code', 'ide', 'editor', 'terminal', 'console', 'git', 'python', 'javascript', 'java', 'vscode', 'intellij', 'sublime'],
                'file_extensions': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.ts', '.jsx', '.tsx', '.go', '.rs'],
                'window_patterns': [r'.*ide.*', r'.*editor.*', r'.*code.*', r'.*terminal.*', r'.*console.*'],
                'min_confidence': 0.6
            },
            'browsing': {
                'keywords': ['chrome', 'firefox', 'edge', 'safari', 'browser', 'web', 'http', 'https'],
                'file_extensions': ['.html', '.htm', '.css', '.js'],
                'window_patterns': [r'.*chrome.*', r'.*firefox.*', r'.*edge.*', r'.*safari.*'],
                'min_confidence': 0.7
            },
            'gaming': {
                'keywords': ['game', 'steam', 'epic', 'origin', 'uplay', 'battle', 'play', 'minecraft', 'valorant', 'csgo'],
                'file_extensions': ['.exe', '.app'],
                'window_patterns': [r'.*game.*', r'.*steam.*', r'.*epic.*'],
                'min_confidence': 0.8
            },
            'productivity': {
                'keywords': ['word', 'excel', 'powerpoint', 'office', 'docs', 'sheets', 'slides', 'notion', 'evernote', 'onenote'],
                'file_extensions': ['.docx', '.xlsx', '.pptx', '.pdf', '.txt', '.md'],
                'window_patterns': [r'.*word.*', r'.*excel.*', r'.*powerpoint.*', r'.*office.*'],
                'min_confidence': 0.6
            },
            'communication': {
                'keywords': ['slack', 'discord', 'teams', 'zoom', 'skype', 'telegram', 'whatsapp', 'outlook', 'mail', 'email'],
                'file_extensions': [],
                'window_patterns': [r'.*slack.*', r'.*discord.*', r'.*teams.*', r'.*zoom.*'],
                'min_confidence': 0.7
            },
            'media': {
                'keywords': ['spotify', 'netflix', 'youtube', 'vlc', 'player', 'music', 'video', 'audio'],
                'file_extensions': ['.mp3', '.mp4', '.avi', '.mkv', '.wav', '.flac'],
                'window_patterns': [r'.*spotify.*', r'.*netflix.*', r'.*youtube.*', r'.*vlc.*'],
                'min_confidence': 0.7
            },
            'development': {
                'keywords': ['docker', 'kubernetes', 'aws', 'azure', 'cloud', 'database', 'sql', 'mongodb', 'redis'],
                'file_extensions': ['.sql', '.dockerfile', '.yaml', '.yml', '.json'],
                'window_patterns': [r'.*docker.*', r'.*kubernetes.*', r'.*aws.*'],
                'min_confidence': 0.6
            },
            'design': {
                'keywords': ['photoshop', 'illustrator', 'figma', 'sketch', 'adobe', 'design', 'creative'],
                'file_extensions': ['.psd', '.ai', '.fig', '.sketch', '.svg', '.png', '.jpg'],
                'window_patterns': [r'.*photoshop.*', r'.*illustrator.*', r'.*figma.*'],
                'min_confidence': 0.7
            }
        }

    def _load_activity_patterns(self) -> Dict[str, Dict]:
        """Load activity detection patterns."""
        return {
            'form_filling': {
                'indicators': ['click', 'type', 'enter', 'tab'],
                'min_events': 5,
                'time_window': 30,
                'pattern': 'alternating_click_type'
            },
            'debugging': {
                'indicators': ['terminal', 'console', 'error', 'debug', 'breakpoint'],
                'min_events': 3,
                'time_window': 60,
                'pattern': 'repeated_terminal_switch'
            },
            'content_creation': {
                'indicators': ['type', 'save', 'format', 'edit'],
                'min_events': 10,
                'time_window': 120,
                'pattern': 'continuous_typing'
            },
            'navigation': {
                'indicators': ['scroll', 'click', 'window_change'],
                'min_events': 5,
                'time_window': 20,
                'pattern': 'rapid_navigation'
            },
            'copy_paste': {
                'indicators': ['copy', 'paste'],
                'min_events': 2,
                'time_window': 10,
                'pattern': 'copy_paste_sequence'
            },
            'search': {
                'indicators': ['type', 'enter', 'click'],
                'min_events': 3,
                'time_window': 15,
                'pattern': 'search_pattern'
            }
        }

    def label_session(self, session_dir: str) -> Optional[LabeledDataset]:
        """Label and categorize a recorded session."""
        if not self.enabled:
            logging.info("Dataset labeling is disabled")
            return None

        logging.info(f"Labeling session: {session_dir}")

        # Load session data
        events = self._load_events(session_dir)
        if not events:
            logging.warning(f"No events found in session: {session_dir}")
            return None

        # Analyze and label
        labeled_data = self._analyze_and_label(events, session_dir)

        # Save labeled dataset
        self._save_labeled_dataset(labeled_data, session_dir)

        return labeled_data

    def _load_events(self, session_dir: str) -> List[Dict]:
        """Load events from the session's CSV file."""
        events = []
        events_csv = os.path.join(session_dir, 'events.csv')

        if not os.path.exists(events_csv):
            logging.warning(f"Events CSV not found: {events_csv}")
            return events

        try:
            with open(events_csv, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    events.append({
                        'timestamp': float(row['Timestamp']),
                        'event_type': row['EventType'],
                        'data': row['Data']
                    })
        except Exception as e:
            logging.error(f"Error loading events: {e}")

        return events

    def _analyze_and_label(self, events: List[Dict], session_dir: str) -> LabeledDataset:
        """Analyze events and generate labels."""
        if not events:
            return None

        # Sort events by timestamp
        events.sort(key=lambda e: e['timestamp'])

        # Extract basic info
        start_time = events[0]['timestamp']
        end_time = events[-1]['timestamp']
        duration = end_time - start_time

        # Categorize session
        categories = self._categorize_session(events)
        primary_category = self._determine_primary_category(categories)

        # Detect activity tags
        activity_tags = self._detect_activities(events)

        # Analyze application usage
        app_usage = self._analyze_application_usage(events)

        # Analyze interaction patterns
        interaction_patterns = self._analyze_interaction_patterns(events)

        # Extract ML features
        ml_features = self._extract_ml_features(events, duration)

        # Create session ID
        session_id = os.path.basename(session_dir)

        return LabeledDataset(
            session_id=session_id,
            start_time=datetime.fromtimestamp(start_time).isoformat(),
            end_time=datetime.fromtimestamp(end_time).isoformat(),
            duration_seconds=duration,
            primary_category=primary_category,
            categories=categories,
            activity_tags=[asdict(tag) for tag in activity_tags],
            application_usage=app_usage,
            interaction_patterns=interaction_patterns,
            ml_features=ml_features,
            metadata={
                'total_events': len(events),
                'event_types': self._count_event_types(events),
                'labeling_timestamp': datetime.now().isoformat(),
                'labeling_version': '1.0'
            }
        )

    def _categorize_session(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Categorize the session into application types."""
        categories = []

        # Extract window titles
        window_titles = set()
        for event in events:
            if event['event_type'] == 'window_change':
                window_titles.add(event['data'].lower())

        # Score each category
        for category_name, category_def in self.categories.items():
            score = 0.0
            matches = []

            # Check keywords
            for keyword in category_def['keywords']:
                for title in window_titles:
                    if keyword in title:
                        score += 0.3
                        matches.append(f"keyword: {keyword}")

            # Check window patterns
            for pattern in category_def['window_patterns']:
                for title in window_titles:
                    if re.search(pattern, title, re.IGNORECASE):
                        score += 0.4
                        matches.append(f"pattern: {pattern}")

            # Normalize score
            confidence = min(score, 1.0)

            if confidence >= category_def['min_confidence']:
                categories.append({
                    'category': category_name,
                    'confidence': confidence,
                    'matches': matches,
                    'description': f"Session appears to be {category_name}-related"
                })

        # Sort by confidence
        categories.sort(key=lambda x: x['confidence'], reverse=True)

        return categories

    def _determine_primary_category(self, categories: List[Dict]) -> str:
        """Determine the primary category from the list."""
        if not categories:
            return 'uncategorized'

        return categories[0]['category']

    def _detect_activities(self, events: List[Dict]) -> List[ActivityTag]:
        """Detect specific activities within the session."""
        activity_tags = []

        for activity_name, activity_def in self.activity_patterns.items():
            detected = self._detect_activity_pattern(events, activity_name, activity_def)
            if detected:
                activity_tags.extend(detected)

        return activity_tags

    def _detect_activity_pattern(self, events: List[Dict], activity_name: str,
                                 activity_def: Dict) -> List[ActivityTag]:
        """Detect a specific activity pattern."""
        detected_activities = []
        time_window = activity_def['time_window']
        min_events = activity_def['min_events']

        # Sliding window detection
        for i in range(len(events)):
            window_events = []
            window_start = events[i]['timestamp']

            # Collect events in time window
            for j in range(i, len(events)):
                if events[j]['timestamp'] - window_start <= time_window:
                    window_events.append(events[j])
                else:
                    break

            if len(window_events) >= min_events:
                # Check for pattern match
                if self._matches_pattern(window_events, activity_def):
                    activity = ActivityTag(
                        tag_name=activity_name,
                        start_time=window_start,
                        end_time=window_events[-1]['timestamp'],
                        duration=window_events[-1]['timestamp'] - window_start,
                        confidence=0.8,
                        context={
                            'event_count': len(window_events),
                            'pattern': activity_def['pattern']
                        }
                    )
                    detected_activities.append(activity)

                    # Skip ahead to avoid overlapping detections
                    i += len(window_events) - 1

        return detected_activities

    def _matches_pattern(self, events: List[Dict], activity_def: Dict) -> bool:
        """Check if events match the activity pattern."""
        pattern = activity_def['pattern']

        if pattern == 'alternating_click_type':
            # Check for alternating click and type events
            event_types = [e['event_type'] for e in events]
            has_click = 'mouse_click' in event_types
            has_type = 'key_press' in event_types
            return has_click and has_type

        elif pattern == 'repeated_terminal_switch':
            # Check for terminal/console window switches
            window_changes = [e for e in events if e['event_type'] == 'window_change']
            terminal_windows = [e for e in window_changes
                              if any(term in e['data'].lower()
                                    for term in ['terminal', 'console', 'cmd', 'bash'])]
            return len(terminal_windows) >= 2

        elif pattern == 'continuous_typing':
            # Check for continuous typing
            key_presses = [e for e in events if e['event_type'] == 'key_press']
            if len(key_presses) < 5:
                return False

            # Check if typing is continuous (short gaps)
            gaps = []
            for i in range(1, len(key_presses)):
                gap = key_presses[i]['timestamp'] - key_presses[i-1]['timestamp']
                gaps.append(gap)

            avg_gap = sum(gaps) / len(gaps)
            return avg_gap < 1.0  # Average gap less than 1 second

        elif pattern == 'rapid_navigation':
            # Check for rapid scrolling and clicking
            scrolls = len([e for e in events if e['event_type'] == 'mouse_scroll'])
            clicks = len([e for e in events if e['event_type'] == 'mouse_click'])
            return scrolls >= 3 or clicks >= 5

        elif pattern == 'copy_paste_sequence':
            # Check for copy followed by paste
            event_sequence = [e['event_type'] for e in events]
            # This is simplified - real implementation would track clipboard events
            return 'key_press' in event_sequence and len(event_sequence) >= 2

        elif pattern == 'search_pattern':
            # Check for type followed by enter
            has_type = any(e['event_type'] == 'key_press' for e in events)
            has_enter = any(e['data'] == 'Key.enter' for e in events if e['event_type'] == 'key_press')
            return has_type and has_enter

        return False

    def _analyze_application_usage(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze application/window usage patterns."""
        window_events = [e for e in events if e['event_type'] == 'window_change']

        if not window_events:
            return {'total_windows': 0, 'window_durations': {}}

        # Calculate window durations
        window_durations = defaultdict(float)
        current_window = None
        window_start_time = None

        for event in window_events:
            if current_window is not None and window_start_time is not None:
                duration = event['timestamp'] - window_start_time
                window_durations[current_window] += duration

            current_window = event['data']
            window_start_time = event['timestamp']

        # Add final window duration
        if current_window and window_start_time:
            duration = events[-1]['timestamp'] - window_start_time
            window_durations[current_window] += duration

        # Calculate statistics
        total_duration = sum(window_durations.values())
        window_percentages = {
            window: (duration / total_duration * 100) if total_duration > 0 else 0
            for window, duration in window_durations.items()
        }

        return {
            'total_windows': len(window_durations),
            'window_durations': dict(window_durations),
            'window_percentages': window_percentages,
            'most_used_window': max(window_durations.items(), key=lambda x: x[1])[0] if window_durations else None
        }

    def _analyze_interaction_patterns(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze interaction patterns in the session."""
        event_types = [e['event_type'] for e in events]
        event_counts = Counter(event_types)

        # Calculate event rates
        if len(events) > 1:
            duration = events[-1]['timestamp'] - events[0]['timestamp']
            if duration > 0:
                event_rates = {
                    event_type: count / duration
                    for event_type, count in event_counts.items()
                }
            else:
                event_rates = {}
        else:
            event_rates = {}

        # Analyze mouse movement patterns
        mouse_moves = [e for e in events if e['event_type'] == 'mouse_move']
        if len(mouse_moves) > 1:
            # Calculate average velocity (simplified)
            total_distance = 0
            for i in range(1, len(mouse_moves)):
                # Parse coordinates from data
                try:
                    prev_data = mouse_moves[i-1]['data']
                    curr_data = mouse_moves[i]['data']
                    # This is simplified - real implementation would parse actual coordinates
                    total_distance += 1  # Placeholder
                except:
                    pass

            avg_velocity = total_distance / len(mouse_moves) if mouse_moves else 0
        else:
            avg_velocity = 0

        return {
            'event_counts': dict(event_counts),
            'event_rates': event_rates,
            'total_events': len(events),
            'mouse_velocity': avg_velocity,
            'dominant_interaction': max(event_counts.items(), key=lambda x: x[1])[0] if event_counts else None
        }

    def _extract_ml_features(self, events: List[Dict], duration: float) -> Dict[str, Any]:
        """Extract features for ML model training."""
        event_counts = Counter(e['event_type'] for e in events)

        # Temporal features
        if duration > 0:
            features = {
                'duration': duration,
                'events_per_second': len(events) / duration,
                'mouse_clicks_per_second': event_counts.get('mouse_click', 0) / duration,
                'key_presses_per_second': event_counts.get('key_press', 0) / duration,
                'scrolls_per_second': event_counts.get('mouse_scroll', 0) / duration,
                'window_changes_per_second': event_counts.get('window_change', 0) / duration,
                'total_mouse_clicks': event_counts.get('mouse_click', 0),
                'total_key_presses': event_counts.get('key_press', 0),
                'total_scrolls': event_counts.get('mouse_scroll', 0),
                'total_window_changes': event_counts.get('window_change', 0),
                'unique_event_types': len(event_counts)
            }
        else:
            features = {
                'duration': 0,
                'events_per_second': 0,
                'mouse_clicks_per_second': 0,
                'key_presses_per_second': 0,
                'scrolls_per_second': 0,
                'window_changes_per_second': 0,
                'total_mouse_clicks': event_counts.get('mouse_click', 0),
                'total_key_presses': event_counts.get('key_press', 0),
                'total_scrolls': event_counts.get('mouse_scroll', 0),
                'total_window_changes': event_counts.get('window_change', 0),
                'unique_event_types': len(event_counts)
            }

        return features

    def _count_event_types(self, events: List[Dict]) -> Dict[str, int]:
        """Count events by type."""
        return dict(Counter(e['event_type'] for e in events))

    def _save_labeled_dataset(self, labeled_data: LabeledDataset, session_dir: str):
        """Save the labeled dataset to a JSON file."""
        if not labeled_data:
            return

        os.makedirs(self.output_dir, exist_ok=True)
        session_id = os.path.basename(session_dir)
        output_file = os.path.join(self.output_dir, f"{session_id}_labeled.json")

        try:
            with open(output_file, 'w') as f:
                json.dump(asdict(labeled_data), f, indent=2)
            logging.info(f"Labeled dataset saved to: {output_file}")
        except Exception as e:
            logging.error(f"Error saving labeled dataset: {e}")

    def batch_label(self, base_dir: str) -> List[LabeledDataset]:
        """Label all sessions in a base directory."""
        labeled_datasets = []

        for item in os.listdir(base_dir):
            session_path = os.path.join(base_dir, item)
            if os.path.isdir(session_path) and item.startswith('session_'):
                labeled = self.label_session(session_path)
                if labeled:
                    labeled_datasets.append(labeled)

        logging.info(f"Labeled {len(labeled_datasets)} sessions")
        return labeled_datasets

    def export_ml_dataset(self, base_dir: str, output_file: str):
        """Export labeled data in ML-ready format."""
        labeled_datasets = self.batch_label(base_dir)

        # Create ML-ready format
        ml_data = {
            'metadata': {
                'total_sessions': len(labeled_datasets),
                'categories': list(self.categories.keys()),
                'activities': list(self.activity_patterns.keys()),
                'export_timestamp': datetime.now().isoformat()
            },
            'sessions': []
        }

        for labeled in labeled_datasets:
            ml_data['sessions'].append({
                'session_id': labeled.session_id,
                'features': labeled.ml_features,
                'labels': {
                    'primary_category': labeled.primary_category,
                    'categories': labeled.categories,
                    'activities': labeled.activity_tags
                },
                'metadata': labeled.metadata
            })

        try:
            with open(output_file, 'w') as f:
                json.dump(ml_data, f, indent=2)
            logging.info(f"ML dataset exported to: {output_file}")
        except Exception as e:
            logging.error(f"Error exporting ML dataset: {e}")


if __name__ == "__main__":
    # Example usage
    labeler = DatasetLabeler()
    labeled = labeler.label_session("dataset/session_20240101_120000")
    if labeled:
        print(json.dumps(asdict(labeled), indent=2))

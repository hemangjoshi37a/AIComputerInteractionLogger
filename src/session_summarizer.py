"""AI-powered session summarization module."""

import os
import json
import logging
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

import cv2
import numpy as np


@dataclass
class ActionEvent:
    """Represents a single action event."""
    timestamp: float
    event_type: str
    data: str
    window_title: Optional[str] = None


@dataclass
class WorkflowStep:
    """Represents a step in a workflow."""
    step_number: int
    action_type: str
    description: str
    timestamp: float
    duration: float
    window_context: Optional[str] = None


@dataclass
class SessionSummary:
    """Structured summary of a recorded session."""
    session_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    total_events: int
    event_breakdown: Dict[str, int]
    windows_visited: List[str]
    workflows: List[Dict[str, Any]]
    key_actions: List[str]
    activity_patterns: Dict[str, Any]
    natural_language_summary: str


class SessionSummarizer:
    """Analyzes recorded sessions and generates AI-powered summaries."""

    def __init__(self, config=None):
        self.config = config or {}
        self.enabled = self.config.get('summarization_enabled', True)
        self.summary_output_dir = self.config.get('summary_output_dir', 'summaries')
        self.use_llm = self.config.get('use_llm_summarization', False)
        self.llm_api_key = self.config.get('llm_api_key', None)
        self.llm_model = self.config.get('llm_model', 'gpt-4')
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)

    def summarize_session(self, session_dir: str) -> SessionSummary:
        """Generate a summary for a recorded session."""
        if not self.enabled:
            logging.info("Summarization is disabled")
            return None

        logging.info(f"Summarizing session: {session_dir}")

        # Load session data
        events = self._load_events(session_dir)
        if not events:
            logging.warning(f"No events found in session: {session_dir}")
            return None

        # Analyze the session
        summary = self._analyze_session(events, session_dir)

        # Save the summary
        self._save_summary(summary, session_dir)

        return summary

    def _load_events(self, session_dir: str) -> List[ActionEvent]:
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
                    event = ActionEvent(
                        timestamp=float(row['Timestamp']),
                        event_type=row['EventType'],
                        data=row['Data']
                    )
                    events.append(event)
        except Exception as e:
            logging.error(f"Error loading events: {e}")

        return events

    def _analyze_session(self, events: List[ActionEvent], session_dir: str) -> SessionSummary:
        """Analyze events and generate a structured summary."""
        if not events:
            return None

        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)

        # Extract basic session info
        start_time = events[0].timestamp
        end_time = events[-1].timestamp
        duration = end_time - start_time

        # Count events by type
        event_breakdown = defaultdict(int)
        for event in events:
            event_breakdown[event.event_type] += 1

        # Extract windows visited
        windows_visited = self._extract_windows(events)

        # Identify workflows
        workflows = self._identify_workflows(events)

        # Extract key actions
        key_actions = self._extract_key_actions(events)

        # Analyze activity patterns
        activity_patterns = self._analyze_activity_patterns(events)

        # Generate natural language summary
        natural_summary = self._generate_natural_summary(
            duration, event_breakdown, windows_visited,
            workflows, key_actions, activity_patterns
        )

        # Create session ID from directory name
        session_id = os.path.basename(session_dir)

        return SessionSummary(
            session_id=session_id,
            start_time=datetime.fromtimestamp(start_time).isoformat(),
            end_time=datetime.fromtimestamp(end_time).isoformat(),
            duration_seconds=duration,
            total_events=len(events),
            event_breakdown=dict(event_breakdown),
            windows_visited=windows_visited,
            workflows=workflows,
            key_actions=key_actions,
            activity_patterns=activity_patterns,
            natural_language_summary=natural_summary
        )

    def _extract_windows(self, events: List[ActionEvent]) -> List[str]:
        """Extract unique windows visited during the session."""
        windows = set()
        for event in events:
            if event.event_type == 'window_change':
                windows.add(event.data)
        return sorted(list(windows))

    def _identify_workflows(self, events: List[ActionEvent]) -> List[Dict[str, Any]]:
        """Identify workflows from the sequence of events."""
        workflows = []
        current_workflow = []
        workflow_start_time = None
        last_event_time = None
        workflow_timeout = 30.0  # seconds

        for event in events:
            if event.event_type in ['mouse_click', 'key_press']:
                if not current_workflow:
                    workflow_start_time = event.timestamp
                    last_event_time = event.timestamp

                # Check if this is a continuation or new workflow
                if last_event_time and (event.timestamp - last_event_time) > workflow_timeout:
                    # Save previous workflow
                    if current_workflow:
                        workflows.append(self._create_workflow_summary(
                            current_workflow, workflow_start_time, last_event_time
                        ))
                    # Start new workflow
                    current_workflow = []
                    workflow_start_time = event.timestamp

                current_workflow.append(event)
                last_event_time = event.timestamp

        # Don't forget the last workflow
        if current_workflow:
            workflows.append(self._create_workflow_summary(
                current_workflow, workflow_start_time, last_event_time
            ))

        return workflows

    def _create_workflow_summary(self, events: List[ActionEvent], start_time: float, end_time: float) -> Dict[str, Any]:
        """Create a summary of a workflow from its events."""
        action_types = defaultdict(int)
        for event in events:
            action_types[event.event_type] += 1

        # Determine the primary action type
        primary_action = max(action_types.items(), key=lambda x: x[1])[0]

        # Generate a description
        description = self._generate_workflow_description(action_types, primary_action)

        return {
            'step_number': len(workflows) + 1 if 'workflows' in locals() else 1,
            'action_type': primary_action,
            'description': description,
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
            'duration': end_time - start_time,
            'event_count': len(events),
            'action_breakdown': dict(action_types)
        }

    def _generate_workflow_description(self, action_types: Dict[str, int], primary_action: str) -> str:
        """Generate a natural language description of a workflow."""
        descriptions = {
            'mouse_click': "Click-based interaction",
            'key_press': "Keyboard input sequence",
            'mouse_move': "Mouse navigation",
            'mouse_scroll': "Scrolling activity"
        }

        base_desc = descriptions.get(primary_action, "Mixed interaction")

        # Add detail about complexity
        total_actions = sum(action_types.values())
        if total_actions < 5:
            complexity = "simple"
        elif total_actions < 15:
            complexity = "moderate"
        else:
            complexity = "complex"

        return f"{complexity} {base_desc} with {total_actions} actions"

    def _extract_key_actions(self, events: List[ActionEvent]) -> List[str]:
        """Extract key actions from the session."""
        key_actions = []

        # Look for significant events
        for event in events:
            if event.event_type == 'key_press':
                if event.data in ['Key.enter', 'Key.tab', 'Key.esc']:
                    key_actions.append(f"Pressed {event.data}")
            elif event.event_type == 'mouse_click':
                key_actions.append(f"Mouse click at {event.data}")
            elif event.event_type == 'window_change':
                key_actions.append(f"Switched to window: {event.data}")

        # Limit to top 10 key actions
        return key_actions[:10]

    def _analyze_activity_patterns(self, events: List[ActionEvent]) -> Dict[str, Any]:
        """Analyze activity patterns in the session."""
        if not events:
            return {}

        # Calculate time between events
        time_intervals = []
        for i in range(1, len(events)):
            interval = events[i].timestamp - events[i-1].timestamp
            time_intervals.append(interval)

        if not time_intervals:
            return {}

        # Calculate statistics
        avg_interval = sum(time_intervals) / len(time_intervals)
        min_interval = min(time_intervals)
        max_interval = max(time_intervals)

        # Determine activity level
        if avg_interval < 0.5:
            activity_level = "high"
        elif avg_interval < 2.0:
            activity_level = "moderate"
        else:
            activity_level = "low"

        return {
            'average_interval': avg_interval,
            'min_interval': min_interval,
            'max_interval': max_interval,
            'activity_level': activity_level,
            'total_active_time': sum(time_intervals),
            'idle_periods': len([i for i in time_intervals if i > 5.0])
        }

    def _generate_natural_summary(
        self,
        duration: float,
        event_breakdown: Dict[str, int],
        windows_visited: List[str],
        workflows: List[Dict[str, Any]],
        key_actions: List[str],
        activity_patterns: Dict[str, Any]
    ) -> str:
        """Generate a natural language summary of the session."""
        # Format duration
        if duration < 60:
            duration_str = f"{duration:.1f} seconds"
        else:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}m {seconds}s"

        # Build summary
        summary_parts = [
            f"This session lasted {duration_str} and recorded {sum(event_breakdown.values())} events.",
            f"The user interacted with {len(windows_visited)} different windows: {', '.join(windows_visited[:5])}."
        ]

        if len(windows_visited) > 5:
            summary_parts[-1] += f", and {len(windows_visited) - 5} others."

        # Add workflow information
        if workflows:
            summary_parts.append(f"The session contained {len(workflows)} distinct workflow segments.")

        # Add activity level
        activity_level = activity_patterns.get('activity_level', 'unknown')
        summary_parts.append(f"Overall activity level was {activity_level}.")

        # Add key actions
        if key_actions:
            summary_parts.append(f"Key actions included: {', '.join(key_actions[:3])}.")

        return " ".join(summary_parts)

    def _save_summary(self, summary: SessionSummary, session_dir: str):
        """Save the summary to a JSON file."""
        if not summary:
            return

        # Create output directory
        os.makedirs(self.summary_output_dir, exist_ok=True)

        # Generate filename
        session_id = os.path.basename(session_dir)
        summary_file = os.path.join(self.summary_output_dir, f"{session_id}_summary.json")

        # Convert to dict and save
        summary_dict = asdict(summary)

        try:
            with open(summary_file, 'w') as f:
                json.dump(summary_dict, f, indent=2)
            logging.info(f"Summary saved to: {summary_file}")
        except Exception as e:
            logging.error(f"Error saving summary: {e}")

    def batch_summarize(self, base_dir: str) -> List[SessionSummary]:
        """Summarize all sessions in a base directory."""
        summaries = []

        for item in os.listdir(base_dir):
            session_path = os.path.join(base_dir, item)
            if os.path.isdir(session_path) and item.startswith('session_'):
                summary = self.summarize_session(session_path)
                if summary:
                    summaries.append(summary)

        logging.info(f"Summarized {len(summaries)} sessions")
        return summaries


if __name__ == "__main__":
    # Example usage
    summarizer = SessionSummarizer()
    summary = summarizer.summarize_session("dataset/session_20240101_120000")
    if summary:
        print(json.dumps(asdict(summary), indent=2))

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
    task_goal: Optional[str] = None
    task_milestones: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None


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

    def _generate_llm_summary(self, timeline_summary: str) -> Optional[Dict[str, Any]]:
        """Call standard Gemini or OpenAI REST endpoints to synthesize goals and subtasks."""
        if not self.llm_api_key:
            logging.warning("use_llm_summarization is True, but llm_api_key is missing in config.")
            return None

        # Build prompt
        prompt = (
            "You are an AI data engineering assistant. Below is a raw sequence of user actions (HCI timeline) "
            "captured during a computer-use session. Your task is to analyze this log and synthesize: \n"
            "1. The high-level task goal (what task was the user trying to accomplish?)\n"
            "2. Step-by-step logical milestones/subtasks.\n"
            "3. Tangible success evaluation criteria.\n"
            "4. A concise natural language narrative summary.\n\n"
            f"HCI Timeline:\n{timeline_summary}\n\n"
            "You MUST respond ONLY with a valid, clean JSON object matching this schema EXACTLY:\n"
            "{\n"
            '  "task_goal": "A single sentence explaining the user\'s high-level task goal.",\n'
            '  "task_milestones": ["Milestone 1...", "Milestone 2..."],\n'
            '  "success_criteria": ["Criteria 1...", "Criteria 2..."],\n'
            '  "summary": "A coherent natural language summary describing the actions taken."\n'
            "}\n"
            "Do not include any extra text, markdown code blocks, or conversational preambles. Output ONLY raw JSON."
        )

        import urllib.request
        import urllib.error
        import time

        model = str(self.llm_model).lower()
        is_gemini = "gemini" in model or "gpt" not in model

        if is_gemini:
            # Standard Gemini API format
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.llm_model}:generateContent?key={self.llm_api_key}"
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            headers = {"Content-Type": "application/json"}
        else:
            # Standard OpenAI API format
            endpoint = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": self.llm_model,
                "messages": [
                    {"role": "system", "content": "You are a precise data engineering assistant that outputs raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.llm_api_key}"
            }

        retries = 3
        backoff = 2.0
        data_bytes = json.dumps(payload).encode('utf-8')

        for attempt in range(retries):
            try:
                req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as response:
                    res_bytes = response.read()
                    res_json = json.loads(res_bytes.decode('utf-8'))

                    if is_gemini:
                        raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        raw_text = res_json["choices"][0]["message"]["content"]

                    raw_text = raw_text.strip()
                    if raw_text.startswith("```"):
                        raw_text = raw_text.split("```")[1]
                        if raw_text.startswith("json"):
                            raw_text = raw_text[4:]
                        raw_text = raw_text.strip()

                    parsed = json.loads(raw_text)
                    return parsed
            except Exception as e:
                logging.warning(f"LLM API Call Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logging.error("All LLM API Call attempts failed. Falling back to rule-based summary.")
        return None

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

        # Generate rule-based default narrative summary
        natural_summary = self._generate_natural_summary(
            duration, event_breakdown, windows_visited,
            workflows, key_actions, activity_patterns
        )

        # Initialize LLM fields
        task_goal = None
        task_milestones = None
        success_criteria = None

        if self.use_llm and self.llm_api_key:
            # Build textual timeline to feed the LLM
            timeline_items = []
            for ev in events[:100]:  # Limit to first 100 relevant events to keep context small and fast
                if ev.event_type in ["mouse_click", "key_press", "window_change"]:
                    elapsed = ev.timestamp - start_time
                    timeline_items.append(f"[{elapsed:.1f}s] {ev.event_type}: {ev.data}")
            timeline_summary = "\n".join(timeline_items)

            llm_result = self._generate_llm_summary(timeline_summary)
            if llm_result:
                task_goal = llm_result.get("task_goal")
                task_milestones = llm_result.get("task_milestones")
                success_criteria = llm_result.get("success_criteria")
                natural_summary = llm_result.get("summary", natural_summary)

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
            natural_language_summary=natural_summary,
            task_goal=task_goal,
            task_milestones=task_milestones,
            success_criteria=success_criteria
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

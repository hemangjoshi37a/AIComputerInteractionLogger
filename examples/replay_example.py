#!/usr/bin/env python3
"""
Example usage of session replay functionality.
"""

import sys
import os
import yaml

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.session_replay import SessionReplay
from src.replay_ui import ReplayUI


def main():
    """Example of session replay usage."""
    # Load config
    config_path = "config.yaml"
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

    # Specify session directory (replace with actual session path)
    session_dir = "dataset/session_20240101_120000"

    # Check if session exists
    if not os.path.exists(session_dir):
        print(f"Session directory not found: {session_dir}")
        print("Please record a session first or update the session_dir path.")
        return

    # Create replay instance
    replay = SessionReplay(session_dir, config)

    try:
        # Load session data
        replay.load_session()

        # Print summary
        summary = replay.get_summary()
        print(f"\nSession Summary:")
        print(f"  Duration: {summary['duration']:.2f} seconds")
        print(f"  Events: {summary['event_count']}")
        print(f"  Screenshots: {summary['screenshot_count']}")
        print(f"  Event Types: {', '.join(summary['event_types'])}")
        print(f"  Window Changes: {summary['window_changes']}")
        print(f"  Mouse Events: {summary['mouse_events']}")
        print(f"  Keyboard Events: {summary['keyboard_events']}")
        print()

        # Get events at specific time
        events_at_time = replay.get_events_at_time(replay.start_time + 5)
        print(f"Events at 5 seconds:")
        for event in events_at_time:
            print(f"  {event['event_type']}: {event['data']}")
        print()

        # Get window changes
        window_changes = replay.get_window_changes()
        print(f"Window Changes ({len(window_changes)}):")
        for change in window_changes[:5]:  # Show first 5
            print(f"  {change['data']}")
        print()

        # Launch UI for visual playback
        print("Launching replay UI...")
        ui = ReplayUI(replay, config)
        ui.setup_ui()
        ui.run()

    except FileNotFoundError as e:
        print(f"Session not found: {e}")
    except Exception as e:
        print(f"Error replaying session: {e}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CLI entry point for session replay.
"""

import argparse
import sys
import os
import logging
import yaml

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.session_replay import SessionReplay
from src.replay_ui import ReplayUI


def replay_session(session_dir, config_path="config.yaml"):
    """Replay a recorded session."""
    # Load config
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

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

        # Create and run UI
        ui = ReplayUI(replay, config)
        ui.setup_ui()
        ui.run()

    except FileNotFoundError as e:
        logging.error(f"Session not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error replaying session: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Replay recorded sessions")
    parser.add_argument("session_dir", help="Path to session directory")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--summary-only", action="store_true", help="Only show session summary")

    args = parser.parse_args()

    if args.summary_only:
        # Load config
        config = {}
        if os.path.exists(args.config):
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)

        # Create replay instance
        replay = SessionReplay(args.session_dir, config)

        try:
            replay.load_session()
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
        except Exception as e:
            logging.error(f"Error loading session: {e}")
            sys.exit(1)
    else:
        replay_session(args.session_dir, args.config)


if __name__ == "__main__":
    main()

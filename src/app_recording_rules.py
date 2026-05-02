"""Application-specific recording rules and configuration."""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class AppRecordingRule:
    """Recording rules for a specific application."""
    app_name: str
    window_patterns: List[str]
    screenshot_frequency: float
    privacy_enabled: bool
    privacy_rules: Dict[str, Any]
    auto_pause: bool
    priority: int  # Higher priority rules take precedence


@dataclass
class RecordingConfig:
    """Current recording configuration."""
    screenshot_frequency: float
    privacy_enabled: bool
    privacy_rules: Dict[str, Any]
    is_paused: bool
    active_app: Optional[str]


class AppRecordingRules:
    """Manages application-specific recording rules."""

    def __init__(self, config=None):
        self.config = config or {}
        self.enabled = self.config.get('app_specific_rules_enabled', True)
        self.rules_file = self.config.get('rules_file', 'app_rules.json')
        self.default_frequency = self.config.get('screenshot_freq', 10)

        # Load rules
        self.rules = self._load_rules()

        # Current state
        self.current_config = RecordingConfig(
            screenshot_frequency=self.default_frequency,
            privacy_enabled=self.config.get('privacy_masking_enabled', False),
            privacy_rules={},
            is_paused=False,
            active_app=None
        )

        # Window tracking
        self.current_window = None
        self.window_history = []

        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)

    def _load_rules(self) -> Dict[str, AppRecordingRule]:
        """Load application recording rules from file."""
        rules = {}

        # Try to load from file
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r') as f:
                    rules_data = json.load(f)

                for app_name, rule_data in rules_data.items():
                    rules[app_name] = AppRecordingRule(
                        app_name=app_name,
                        window_patterns=rule_data.get('window_patterns', []),
                        screenshot_frequency=rule_data.get('screenshot_frequency', self.default_frequency),
                        privacy_enabled=rule_data.get('privacy_enabled', False),
                        privacy_rules=rule_data.get('privacy_rules', {}),
                        auto_pause=rule_data.get('auto_pause', False),
                        priority=rule_data.get('priority', 0)
                    )

                logging.info(f"Loaded {len(rules)} application rules from {self.rules_file}")
            except Exception as e:
                logging.error(f"Error loading rules file: {e}")

        # Add default rules if none exist
        if not rules:
            rules = self._get_default_rules()
            self._save_rules(rules)

        return rules

    def _get_default_rules(self) -> Dict[str, AppRecordingRule]:
        """Get default application recording rules."""
        return {
            'browser': AppRecordingRule(
                app_name='browser',
                window_patterns=[r'.*chrome.*', r'.*firefox.*', r'.*edge.*', r'.*safari.*'],
                screenshot_frequency=5.0,
                privacy_enabled=True,
                privacy_rules={
                    'mask_password_fields': True,
                    'mask_emails': True,
                    'mask_credit_cards': True,
                    'mask_urls': False
                },
                auto_pause=False,
                priority=1
            ),
            'ide': AppRecordingRule(
                app_name='ide',
                window_patterns=[r'.*vscode.*', r'.*intellij.*', r'.*pycharm.*', r'.*visual studio.*'],
                screenshot_frequency=2.0,
                privacy_enabled=False,
                privacy_rules={},
                auto_pause=False,
                priority=2
            ),
            'terminal': AppRecordingRule(
                app_name='terminal',
                window_patterns=[r'.*terminal.*', r'.*console.*', r'.*cmd.*', r'.*powershell.*', r'.*bash.*'],
                screenshot_frequency=1.0,
                privacy_enabled=True,
                privacy_rules={
                    'mask_password_fields': True,
                    'mask_api_keys': True,
                    'mask_ip_addresses': True
                },
                auto_pause=False,
                priority=2
            ),
            'banking': AppRecordingRule(
                app_name='banking',
                window_patterns=[r'.*bank.*', r'.*finance.*', r'.*payment.*', r'.*transaction.*'],
                screenshot_frequency=0.5,
                privacy_enabled=True,
                privacy_rules={
                    'mask_password_fields': True,
                    'mask_emails': True,
                    'mask_credit_cards': True,
                    'mask_phone_numbers': True,
                    'mask_ssn': True,
                    'blur_strength': 50
                },
                auto_pause=True,
                priority=10
            ),
            'password_manager': AppRecordingRule(
                app_name='password_manager',
                window_patterns=[r'.*password.*', r'.*credential.*', r'.*1password.*', r'.*lastpass.*', r'.*bitwarden.*'],
                screenshot_frequency=0.1,
                privacy_enabled=True,
                privacy_rules={
                    'mask_password_fields': True,
                    'blur_strength': 100
                },
                auto_pause=True,
                priority=10
            ),
            'communication': AppRecordingRule(
                app_name='communication',
                window_patterns=[r'.*slack.*', r'.*discord.*', r'.*teams.*', r'.*zoom.*', r'.*skype.*'],
                screenshot_frequency=3.0,
                privacy_enabled=True,
                privacy_rules={
                    'mask_emails': True,
                    'mask_phone_numbers': True
                },
                auto_pause=False,
                priority=1
            ),
            'media': AppRecordingRule(
                app_name='media',
                window_patterns=[r'.*spotify.*', r'.*netflix.*', r'.*youtube.*', r'.*vlc.*', r'.*player.*'],
                screenshot_frequency=0.5,
                privacy_enabled=False,
                privacy_rules={},
                auto_pause=False,
                priority=0
            ),
            'gaming': AppRecordingRule(
                app_name='gaming',
                window_patterns=[r'.*game.*', r'.*steam.*', r'.*epic.*', r'.*origin.*'],
                screenshot_frequency=30.0,
                privacy_enabled=False,
                privacy_rules={},
                auto_pause=False,
                priority=0
            )
        }

    def _save_rules(self, rules: Dict[str, AppRecordingRule]):
        """Save rules to file."""
        try:
            rules_data = {}
            for app_name, rule in rules.items():
                rules_data[app_name] = asdict(rule)

            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)

            logging.info(f"Saved {len(rules)} application rules to {self.rules_file}")
        except Exception as e:
            logging.error(f"Error saving rules file: {e}")

    def update_window(self, window_title: str) -> RecordingConfig:
        """Update recording configuration based on current window."""
        if not self.enabled:
            return self.current_config

        self.current_window = window_title
        self.window_history.append(window_title)

        # Find matching rule
        matched_rule = self._find_matching_rule(window_title)

        if matched_rule:
            logging.info(f"Matched rule for '{window_title}': {matched_rule.app_name}")

            # Update configuration
            self.current_config = RecordingConfig(
                screenshot_frequency=matched_rule.screenshot_frequency,
                privacy_enabled=matched_rule.privacy_enabled,
                privacy_rules=matched_rule.privacy_rules,
                is_paused=matched_rule.auto_pause,
                active_app=matched_rule.app_name
            )

            if matched_rule.auto_pause:
                logging.warning(f"Recording paused for sensitive app: {matched_rule.app_name}")
        else:
            # Use default configuration
            self.current_config = RecordingConfig(
                screenshot_frequency=self.default_frequency,
                privacy_enabled=self.config.get('privacy_masking_enabled', False),
                privacy_rules={},
                is_paused=False,
                active_app=None
            )

        return self.current_config

    def _find_matching_rule(self, window_title: str) -> Optional[AppRecordingRule]:
        """Find the best matching rule for a window title."""
        if not window_title:
            return None

        window_lower = window_title.lower()
        matched_rules = []

        for rule in self.rules.values():
            for pattern in rule.window_patterns:
                if re.search(pattern, window_lower, re.IGNORECASE):
                    matched_rules.append(rule)
                    break

        if not matched_rules:
            return None

        # Return rule with highest priority
        return max(matched_rules, key=lambda r: r.priority)

    def get_current_config(self) -> RecordingConfig:
        """Get the current recording configuration."""
        return self.current_config

    def add_rule(self, rule: AppRecordingRule):
        """Add or update a recording rule."""
        self.rules[rule.app_name] = rule
        self._save_rules(self.rules)
        logging.info(f"Added/updated rule for: {rule.app_name}")

    def remove_rule(self, app_name: str):
        """Remove a recording rule."""
        if app_name in self.rules:
            del self.rules[app_name]
            self._save_rules(self.rules)
            logging.info(f"Removed rule for: {app_name}")

    def get_rule(self, app_name: str) -> Optional[AppRecordingRule]:
        """Get a specific recording rule."""
        return self.rules.get(app_name)

    def list_rules(self) -> List[Dict[str, Any]]:
        """List all recording rules."""
        return [asdict(rule) for rule in self.rules.values()]

    def get_app_statistics(self) -> Dict[str, Any]:
        """Get statistics about application usage."""
        if not self.window_history:
            return {}

        app_counts = defaultdict(int)
        for window in self.window_history:
            rule = self._find_matching_rule(window)
            if rule:
                app_counts[rule.app_name] += 1
            else:
                app_counts['other'] += 1

        total = sum(app_counts.values())
        app_percentages = {
            app: (count / total * 100) if total > 0 else 0
            for app, count in app_counts.items()
        }

        return {
            'total_windows': len(self.window_history),
            'app_counts': dict(app_counts),
            'app_percentages': app_percentages,
            'most_used_app': max(app_counts.items(), key=lambda x: x[1])[0] if app_counts else None
        }

    def reset_statistics(self):
        """Reset usage statistics."""
        self.window_history = []
        logging.info("Reset application usage statistics")

    def export_rules(self, output_file: str):
        """Export rules to a file."""
        self._save_rules(self.rules)
        logging.info(f"Rules exported to: {output_file}")

    def import_rules(self, input_file: str):
        """Import rules from a file."""
        try:
            with open(input_file, 'r') as f:
                rules_data = json.load(f)

            for app_name, rule_data in rules_data.items():
                self.rules[app_name] = AppRecordingRule(
                    app_name=app_name,
                    window_patterns=rule_data.get('window_patterns', []),
                    screenshot_frequency=rule_data.get('screenshot_frequency', self.default_frequency),
                    privacy_enabled=rule_data.get('privacy_enabled', False),
                    privacy_rules=rule_data.get('privacy_rules', {}),
                    auto_pause=rule_data.get('auto_pause', False),
                    priority=rule_data.get('priority', 0)
                )

            logging.info(f"Imported {len(rules_data)} rules from: {input_file}")
        except Exception as e:
            logging.error(f"Error importing rules: {e}")


if __name__ == "__main__":
    # Example usage
    rules_manager = AppRecordingRules()

    # Test window matching
    test_windows = [
        "Google Chrome - YouTube",
        "Visual Studio Code - main.py",
        "Terminal - bash",
        "Chase Online Banking",
        "1Password - Password Manager"
    ]

    for window in test_windows:
        config = rules_manager.update_window(window)
        print(f"Window: {window}")
        print(f"  App: {config.active_app}")
        print(f"  Frequency: {config.screenshot_frequency} fps")
        print(f"  Privacy: {config.privacy_enabled}")
        print(f"  Paused: {config.is_paused}")
        print()

    # Get statistics
    stats = rules_manager.get_app_statistics()
    print("Application Statistics:")
    print(json.dumps(stats, indent=2))

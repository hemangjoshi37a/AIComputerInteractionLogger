"""Real-time anomaly detection for computer interaction sessions."""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import statistics

import numpy as np


@dataclass
class AnomalyEvent:
    """Represents a detected anomaly."""
    timestamp: float
    anomaly_type: str
    severity: str  # low, medium, high, critical
    description: str
    context: Dict[str, Any]
    confidence: float


@dataclass
class AnomalyReport:
    """Complete anomaly report for a session."""
    session_id: str
    start_time: str
    end_time: str
    total_anomalies: int
    anomalies_by_type: Dict[str, int]
    anomalies_by_severity: Dict[str, int]
    anomalies: List[Dict[str, Any]]
    security_incidents: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]
    recommendations: List[str]


class AnomalyDetector:
    """Detects anomalies in real-time during recording sessions."""

    def __init__(self, config=None):
        self.config = config or {}
        self.enabled = self.config.get('anomaly_detection_enabled', True)
        self.sensitivity = self.config.get('anomaly_sensitivity', 'medium')  # low, medium, high
        self.alert_threshold = self.config.get('alert_threshold', 'high')  # minimum severity to alert
        self.output_dir = self.config.get('anomaly_output_dir', 'anomalies')

        # Detection windows
        self.event_window_size = self.config.get('event_window_size', 100)
        self.time_window_seconds = self.config.get('time_window_seconds', 30)

        # State tracking
        self.event_history = deque(maxlen=self.event_window_size)
        self.anomalies = []
        self.session_start_time = None
        self.last_alert_time = 0
        self.alert_cooldown = self.config.get('alert_cooldown', 60)  # seconds

        # Baseline statistics
        self.baseline_stats = {
            'mouse_click_rate': 0,
            'key_press_rate': 0,
            'scroll_rate': 0,
            'window_switch_rate': 0,
            'avg_mouse_velocity': 0
        }

        # Security patterns
        self.security_patterns = self._load_security_patterns()

        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)

    def _load_security_patterns(self) -> Dict[str, Any]:
        """Load security-related patterns for detection."""
        return {
            'rapid_credential_entry': {
                'enabled': self.config.get('detect_rapid_credentials', True),
                'threshold': self.config.get('credential_entry_threshold', 5),  # keys per second
                'window': self.config.get('credential_entry_window', 3)  # seconds
            },
            'unusual_navigation': {
                'enabled': self.config.get('detect_unusual_navigation', True),
                'window_switch_threshold': self.config.get('window_switch_threshold', 10),  # per minute
                'sensitive_apps': self.config.get('sensitive_applications', [
                    'bank', 'finance', 'password', 'credential', 'login'
                ])
            },
            'suspicious_copy_paste': {
                'enabled': self.config.get('detect_suspicious_copy_paste', True),
                'threshold': self.config.get('copy_paste_threshold', 3)  # per minute
            },
            'unusual_access_times': {
                'enabled': self.config.get('detect_unusual_times', True),
                'normal_hours': self.config.get('normal_working_hours', (9, 17))  # 9 AM to 5 PM
            }
        }

    def start_session(self):
        """Start a new detection session."""
        self.session_start_time = time.time()
        self.event_history.clear()
        self.anomalies = []
        logging.info("Anomaly detection session started")

    def process_event(self, event_type: str, timestamp: float, data: Any):
        """Process an event and check for anomalies."""
        if not self.enabled:
            return

        # Add to history
        self.event_history.append({
            'type': event_type,
            'timestamp': timestamp,
            'data': data
        })

        # Check for anomalies
        self._check_for_anomalies(timestamp)

    def _check_for_anomalies(self, current_time: float):
        """Check current state for anomalies."""
        if len(self.event_history) < 10:
            return

        # Get recent events
        recent_events = self._get_recent_events(current_time - self.time_window_seconds)

        # Check various anomaly types
        self._check_rapid_activity(current_time, recent_events)
        self._check_security_incidents(current_time, recent_events)
        self._check_performance_issues(current_time, recent_events)
        self._check_unusual_patterns(current_time, recent_events)

    def _get_recent_events(self, since_timestamp: float) -> List[Dict]:
        """Get events since a given timestamp."""
        return [e for e in self.event_history if e['timestamp'] >= since_timestamp]

    def _check_rapid_activity(self, current_time: float, recent_events: List[Dict]):
        """Check for unusually rapid activity."""
        if not recent_events:
            return

        # Calculate rates
        time_span = current_time - recent_events[0]['timestamp'] if recent_events else 1
        if time_span < 1:
            time_span = 1

        event_counts = defaultdict(int)
        for event in recent_events:
            event_counts[event['type']] += 1

        # Check for rapid clicking
        click_rate = event_counts['mouse_click'] / time_span
        if click_rate > self._get_threshold('rapid_click_rate', 10):
            self._add_anomaly(
                current_time,
                'rapid_clicking',
                self._calculate_severity(click_rate, 10, 20),
                f"Unusually high click rate: {click_rate:.1f} clicks/second",
                {'click_rate': click_rate, 'threshold': 10}
            )

        # Check for rapid typing
        key_rate = event_counts['key_press'] / time_span
        if key_rate > self._get_threshold('rapid_typing_rate', 15):
            self._add_anomaly(
                current_time,
                'rapid_typing',
                self._calculate_severity(key_rate, 15, 25),
                f"Unusually high typing rate: {key_rate:.1f} keys/second",
                {'key_rate': key_rate, 'threshold': 15}
            )

    def _check_security_incidents(self, current_time: float, recent_events: List[Dict]):
        """Check for potential security incidents."""
        patterns = self.security_patterns

        # Check for rapid credential entry
        if patterns['rapid_credential_entry']['enabled']:
            key_events = [e for e in recent_events if e['type'] == 'key_press']
            if len(key_events) > 0:
                time_span = current_time - key_events[0]['timestamp']
                if time_span > 0:
                    rate = len(key_events) / time_span
                    threshold = patterns['rapid_credential_entry']['threshold']
                    if rate > threshold:
                        self._add_anomaly(
                            current_time,
                            'potential_credential_harvesting',
                            'high',
                            f"Rapid keyboard input detected: {rate:.1f} keys/second",
                            {'key_rate': rate, 'threshold': threshold}
                        )

        # Check for unusual window switching
        if patterns['unusual_navigation']['enabled']:
            window_events = [e for e in recent_events if e['type'] == 'window_change']
            if len(window_events) > patterns['unusual_navigation']['window_switch_threshold']:
                self._add_anomaly(
                    current_time,
                    'unusual_window_switching',
                    'medium',
                    f"Excessive window switching: {len(window_events)} switches in {self.time_window_seconds}s",
                    {'switch_count': len(window_events)}
                )

    def _check_performance_issues(self, current_time: float, recent_events: List[Dict]):
        """Check for performance-related issues."""
        # Check for idle periods followed by bursts
        if len(self.event_history) > 20:
            # Look for idle periods
            idle_threshold = 5.0  # seconds
            idle_periods = 0

            for i in range(len(self.event_history) - 1):
                gap = self.event_history[i + 1]['timestamp'] - self.event_history[i]['timestamp']
                if gap > idle_threshold:
                    idle_periods += 1

            if idle_periods > 3:
                self._add_anomaly(
                    current_time,
                    'intermittent_activity',
                    'low',
                    f"Multiple idle periods detected: {idle_periods} pauses",
                    {'idle_periods': idle_periods}
                )

    def _check_unusual_patterns(self, current_time: float, recent_events: List[Dict]):
        """Check for unusual behavioral patterns."""
        if len(recent_events) < 5:
            return

        # Check for repetitive actions
        action_sequence = [e['type'] for e in recent_events]
        if len(action_sequence) >= 4:
            # Check for repeated patterns
            for i in range(len(action_sequence) - 3):
                pattern = action_sequence[i:i+2]
                next_pattern = action_sequence[i+2:i+4]
                if pattern == next_pattern:
                    self._add_anomaly(
                        current_time,
                        'repetitive_behavior',
                        'low',
                        f"Repetitive action pattern detected: {pattern}",
                        {'pattern': pattern}
                    )
                    break

    def _get_threshold(self, name: str, default: float) -> float:
        """Get threshold value based on sensitivity."""
        multipliers = {
            'low': 2.0,
            'medium': 1.0,
            'high': 0.5
        }
        return default * multipliers.get(self.sensitivity, 1.0)

    def _calculate_severity(self, value: float, medium_threshold: float, high_threshold: float) -> str:
        """Calculate severity based on value and thresholds."""
        if value >= high_threshold:
            return 'high'
        elif value >= medium_threshold:
            return 'medium'
        else:
            return 'low'

    def _add_anomaly(self, timestamp: float, anomaly_type: str, severity: str,
                     description: str, context: Dict[str, Any], confidence: float = 0.8):
        """Add an anomaly to the list."""
        anomaly = AnomalyEvent(
            timestamp=timestamp,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            context=context,
            confidence=confidence
        )

        self.anomalies.append(anomaly)

        # Log the anomaly
        logging.warning(f"Anomaly detected: {anomaly_type} ({severity}) - {description}")

        # Check if we should alert
        if self._should_alert(severity):
            self._send_alert(anomaly)

    def _should_alert(self, severity: str) -> bool:
        """Determine if an alert should be sent."""
        severity_levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        alert_levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}

        current_level = severity_levels.get(severity, 0)
        threshold_level = alert_levels.get(self.alert_threshold, 2)

        # Check cooldown
        if time.time() - self.last_alert_time < self.alert_cooldown:
            return False

        return current_level >= threshold_level

    def _send_alert(self, anomaly: AnomalyEvent):
        """Send an alert for the anomaly."""
        self.last_alert_time = time.time()

        # In a real implementation, this could send to:
        # - Desktop notification
        # - Email
        # - Slack/Discord webhook
        # - Logging system

        alert_message = (
            f"🚨 SECURITY ALERT\n"
            f"Type: {anomaly.anomaly_type}\n"
            f"Severity: {anomaly.severity}\n"
            f"Description: {anomaly.description}\n"
            f"Time: {datetime.fromtimestamp(anomaly.timestamp).isoformat()}"
        )

        logging.critical(alert_message)
        print(f"\n{alert_message}\n")

    def generate_report(self, session_id: str) -> AnomalyReport:
        """Generate a complete anomaly report."""
        if not self.session_start_time:
            return None

        end_time = time.time()

        # Categorize anomalies
        anomalies_by_type = defaultdict(int)
        anomalies_by_severity = defaultdict(int)
        security_incidents = []
        performance_issues = []

        for anomaly in self.anomalies:
            anomalies_by_type[anomaly.anomaly_type] += 1
            anomalies_by_severity[anomaly.severity] += 1

            # Categorize by type
            if 'credential' in anomaly.anomaly_type or 'security' in anomaly.anomaly_type:
                security_incidents.append(asdict(anomaly))
            elif 'performance' in anomaly.anomaly_type or 'idle' in anomaly.anomaly_type:
                performance_issues.append(asdict(anomaly))

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return AnomalyReport(
            session_id=session_id,
            start_time=datetime.fromtimestamp(self.session_start_time).isoformat(),
            end_time=datetime.fromtimestamp(end_time).isoformat(),
            total_anomalies=len(self.anomalies),
            anomalies_by_type=dict(anomalies_by_type),
            anomalies_by_severity=dict(anomalies_by_severity),
            anomalies=[asdict(a) for a in self.anomalies],
            security_incidents=security_incidents,
            performance_issues=performance_issues,
            recommendations=recommendations
        )

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on detected anomalies."""
        recommendations = []

        if not self.anomalies:
            recommendations.append("No anomalies detected. Session appears normal.")
            return recommendations

        # Analyze anomaly types
        anomaly_types = [a.anomaly_type for a in self.anomalies]

        if 'rapid_clicking' in anomaly_types:
            recommendations.append("Consider reviewing automated clicking behavior or bot detection.")

        if 'rapid_typing' in anomaly_types:
            recommendations.append("Monitor for potential automated input or credential harvesting.")

        if 'potential_credential_harvesting' in anomaly_types:
            recommendations.append("URGENT: Review session for potential security breach.")

        if 'unusual_window_switching' in anomaly_types:
            recommendations.append("Investigate rapid application switching patterns.")

        if len([a for a in self.anomalies if a.severity in ['high', 'critical']]) > 0:
            recommendations.append("High-severity anomalies detected. Immediate review recommended.")

        return recommendations

    def save_report(self, report: AnomalyReport):
        """Save the anomaly report to a JSON file."""
        if not report:
            return

        os.makedirs(self.output_dir, exist_ok=True)
        report_file = os.path.join(self.output_dir, f"{report.session_id}_anomalies.json")

        try:
            with open(report_file, 'w') as f:
                json.dump(asdict(report), f, indent=2)
            logging.info(f"Anomaly report saved to: {report_file}")
        except Exception as e:
            logging.error(f"Error saving anomaly report: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get current detection statistics."""
        return {
            'session_duration': time.time() - self.session_start_time if self.session_start_time else 0,
            'total_events': len(self.event_history),
            'total_anomalies': len(self.anomalies),
            'anomalies_by_type': {k: len([a for a in self.anomalies if a.anomaly_type == k])
                                  for k in set(a.anomaly_type for a in self.anomalies)},
            'anomalies_by_severity': {k: len([a for a in self.anomalies if a.severity == k])
                                     for k in set(a.severity for a in self.anomalies)}
        }


if __name__ == "__main__":
    # Example usage
    detector = AnomalyDetector()
    detector.start_session()

    # Simulate some events
    current_time = time.time()
    for i in range(20):
        detector.process_event('mouse_click', current_time + i * 0.1, f"click_{i}")

    # Generate report
    report = detector.generate_report("test_session")
    if report:
        print(json.dumps(asdict(report), indent=2))

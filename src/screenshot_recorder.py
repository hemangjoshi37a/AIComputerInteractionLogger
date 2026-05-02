import threading
import time
import logging
import pyscreenshot as ImageGrab
import numpy as np
import cv2
from collections import deque
from .privacy_masker import PrivacyMasker

class ScreenshotRecorder:
    def __init__(self, output_queue, frequency, config=None):
        self.output_queue = output_queue
        self.base_frequency = frequency
        self.config = config or {}
        self.running = False

        # Smart triggering settings
        self.smart_triggering = self.config.get('smart_screenshot_triggering', False)
        self.motion_threshold = self.config.get('motion_threshold', 0.01)
        self.min_screenshot_interval = self.config.get('min_screenshot_interval', 1.0)
        self.last_screenshot = None
        self.last_screenshot_time = 0

        # Activity-based adaptive recording settings
        self.adaptive_recording = self.config.get('adaptive_recording_enabled', False)
        self.idle_threshold = self.config.get('idle_threshold', 0.005)  # Lower threshold for idle detection
        self.high_activity_threshold = self.config.get('high_activity_threshold', 0.05)  # Higher threshold for high activity
        self.idle_frequency = self.config.get('idle_frequency', 1.0)  # 1 fps when idle
        self.high_activity_frequency = self.config.get('high_activity_frequency', 30.0)  # 30 fps during high activity
        self.activity_window = self.config.get('activity_window', 5)  # Number of frames to analyze for activity level
        self.activity_history = deque(maxlen=self.activity_window)
        self.current_frequency = self.base_frequency

        # Privacy masking
        self.privacy_masker = PrivacyMasker(self.config)

    def start(self):
        self.running = True
        threading.Thread(target=self._record, daemon=True).start()
        logging.info("Screenshot recorder started")

    def stop(self):
        self.running = False
        logging.info("Screenshot recorder stopped")

    def _record(self):
        while self.running:
            try:
                screenshot = ImageGrab.grab()
                screenshot_np = np.array(screenshot)

                # Apply privacy masking
                screenshot_np = self.privacy_masker.mask_screenshot(screenshot_np)

                current_time = time.time()

                if self.adaptive_recording:
                    # Calculate activity level
                    activity_level = self._calculate_activity_level(screenshot_np)
                    self.activity_history.append(activity_level)

                    # Adjust frequency based on activity
                    self._adjust_frequency()

                    # Determine if we should capture this frame
                    if self._should_capture_frame(current_time):
                        self.output_queue.put(('screenshot', current_time, screenshot_np))
                        self.last_screenshot = screenshot_np
                        self.last_screenshot_time = current_time
                        logging.debug(f"Screenshot captured (activity: {activity_level:.4f}, freq: {self.current_frequency:.1f} fps)")
                elif self.smart_triggering:
                    if (self._detect_motion(screenshot_np) and
                        current_time - self.last_screenshot_time >= self.min_screenshot_interval):
                        self.output_queue.put(('screenshot', current_time, screenshot_np))
                        self.last_screenshot = screenshot_np
                        self.last_screenshot_time = current_time
                        logging.debug(f"Screenshot captured (motion detected)")
                else:
                    self.output_queue.put(('screenshot', current_time, screenshot_np))

                # Sleep based on current frequency
                sleep_time = 1.0 / self.current_frequency
                time.sleep(sleep_time)
            except Exception as e:
                logging.error(f"Screenshot error: {e}")
                time.sleep(1)  # Prevent rapid error logging

    def _calculate_activity_level(self, current_frame):
        """Calculate the activity level based on frame difference."""
        if self.last_screenshot is None:
            return 0.0

        # Calculate difference
        diff = cv2.absdiff(self.last_screenshot, current_frame)
        diff_ratio = np.count_nonzero(diff) / diff.size
        return diff_ratio

    def _adjust_frequency(self):
        """Adjust capture frequency based on recent activity levels."""
        if len(self.activity_history) < self.activity_window:
            return

        avg_activity = sum(self.activity_history) / len(self.activity_history)

        if avg_activity <= self.idle_threshold:
            # Idle state - reduce frequency
            self.current_frequency = self.idle_frequency
        elif avg_activity >= self.high_activity_threshold:
            # High activity - increase frequency
            self.current_frequency = self.high_activity_frequency
        else:
            # Normal activity - use base frequency
            self.current_frequency = self.base_frequency

    def _should_capture_frame(self, current_time):
        """Determine if a frame should be captured based on timing."""
        time_since_last = current_time - self.last_screenshot_time
        return time_since_last >= (1.0 / self.current_frequency)

    def _detect_motion(self, current_frame):
        """Detect if current frame differs significantly from last frame."""
        if self.last_screenshot is None:
            return True

        # Calculate difference
        diff = cv2.absdiff(self.last_screenshot, current_frame)
        diff_ratio = np.count_nonzero(diff) / diff.size

        return diff_ratio >= self.motion_threshold

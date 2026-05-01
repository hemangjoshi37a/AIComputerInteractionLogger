import threading
import time
import logging
import pyscreenshot as ImageGrab
import numpy as np
import cv2
from .privacy_masker import PrivacyMasker

class ScreenshotRecorder:
    def __init__(self, output_queue, frequency, config=None):
        self.output_queue = output_queue
        self.frequency = frequency
        self.config = config or {}
        self.running = False

        # Smart triggering settings
        self.smart_triggering = self.config.get('smart_screenshot_triggering', False)
        self.motion_threshold = self.config.get('motion_threshold', 0.01)
        self.min_screenshot_interval = self.config.get('min_screenshot_interval', 1.0)
        self.last_screenshot = None
        self.last_screenshot_time = 0

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

                if self.smart_triggering:
                    current_time = time.time()
                    if (self._detect_motion(screenshot_np) and
                        current_time - self.last_screenshot_time >= self.min_screenshot_interval):
                        self.output_queue.put(('screenshot', current_time, screenshot_np))
                        self.last_screenshot = screenshot_np
                        self.last_screenshot_time = current_time
                        logging.debug(f"Screenshot captured (motion detected)")
                else:
                    self.output_queue.put(('screenshot', time.time(), screenshot_np))

                time.sleep(1 / self.frequency)
            except Exception as e:
                logging.error(f"Screenshot error: {e}")
                time.sleep(1)  # Prevent rapid error logging

    def _detect_motion(self, current_frame):
        """Detect if current frame differs significantly from last frame."""
        if self.last_screenshot is None:
            return True

        # Calculate difference
        diff = cv2.absdiff(self.last_screenshot, current_frame)
        diff_ratio = np.count_nonzero(diff) / diff.size

        return diff_ratio >= self.motion_threshold

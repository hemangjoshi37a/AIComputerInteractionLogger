import threading
import time
import logging
import pyscreenshot as ImageGrab
import numpy as np

class ScreenshotRecorder:
    def __init__(self, output_queue, frequency):
        self.output_queue = output_queue
        self.frequency = frequency
        self.running = False

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
                self.output_queue.put(('screenshot', time.time(), screenshot_np))
                time.sleep(1 / self.frequency)
            except Exception as e:
                logging.error(f"Screenshot error: {e}")
                time.sleep(1)  # Prevent rapid error logging

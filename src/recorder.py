import os
import time
import csv
import queue
import threading
import logging
from datetime import datetime

from .screenshot_recorder import ScreenshotRecorder
from .mouse_keyboard_recorder import MouseKeyboardRecorder
from .audio_recorder import AudioRecorder

class DatasetRecorder:
    def __init__(self, base_output_dir="dataset", screenshot_freq=10):
        self.base_output_dir = base_output_dir
        self.screenshot_freq = screenshot_freq
        self.data_queue = queue.Queue()
        self.running = False
        self.session_dir = None
        self.save_thread = None
        self.csv_file = None
        self.csv_writer = None

    def start_recording(self, duration):
        self.session_dir = self._create_session_dir()
        self.running = True
        self.csv_file = open(os.path.join(self.session_dir, "events.csv"), 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Timestamp", "EventType", "Data"])

        self.screenshot_recorder = ScreenshotRecorder(self.data_queue, self.screenshot_freq)
        self.mouse_keyboard_recorder = MouseKeyboardRecorder(self.data_queue)
        self.audio_recorder = AudioRecorder(self.data_queue)

        self.screenshot_recorder.start()
        self.mouse_keyboard_recorder.start()
        self.audio_recorder.start()

        self.save_thread = threading.Thread(target=self._save_data, daemon=True)
        self.save_thread.start()

        logging.info(f"Recording started for {duration} seconds...")
        time.sleep(duration)

        self.stop_recording()

    def stop_recording(self):
        logging.info("Stopping recording...")
        self.running = False
        self.screenshot_recorder.stop()
        self.mouse_keyboard_recorder.stop()
        self.audio_recorder.stop()
        self.flush_data()
        if self.save_thread:
            self.save_thread.join()
        if self.csv_file:
            self.csv_file.close()
        logging.info("Recording stopped and data saved.")

    def flush_data(self):
        logging.info("Flushing remaining data...")
        while not self.data_queue.empty():
            try:
                event_type, timestamp, data = self.data_queue.get(block=False)
                self._process_event(event_type, timestamp, data)
            except queue.Empty:
                break
        logging.info("Data flush completed.")

    def _create_session_dir(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.base_output_dir, f"session_{timestamp}")
        os.makedirs(session_dir, exist_ok=True)
        return session_dir

    def _save_data(self):
        while self.running or not self.data_queue.empty():
            try:
                event_type, timestamp, data = self.data_queue.get(timeout=1)
                self._process_event(event_type, timestamp, data)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error saving data: {e}")

    def _process_event(self, event_type, timestamp, data):
        if event_type == 'screenshot':
            filename = f"screenshot_{int(timestamp)}.png"
            img_path = os.path.join(self.session_dir, filename)
            data.save(img_path)
            self.csv_writer.writerow([timestamp, event_type, filename])
        else:
            self.csv_writer.writerow([timestamp, event_type, data])
        logging.debug(f"Recorded event: {event_type} at {timestamp}")

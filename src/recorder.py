import os
import time
import csv
import queue
import threading
import logging
from datetime import datetime
import yaml

import numpy as np
import cv2
import wave
import sounddevice as sd

from .screenshot_recorder import ScreenshotRecorder
from .mouse_keyboard_recorder import MouseKeyboardRecorder
from .audio_recorder import AudioRecorder

class DatasetRecorder:
    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)
        self.base_output_dir = self.config['base_output_dir']
        self.screenshot_freq = self.config['screenshot_freq']
        self.data_queue = queue.Queue()
        self.running = False
        self.session_dir = None
        self.save_thread = None
        self.csv_file = None
        self.csv_writer = None
        self.audio_file = None
        self.audio_writer = None
        self.setup_logging()

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def setup_logging(self):
        logging.basicConfig(level=self.config['log_level'],
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            filename=os.path.join(self.base_output_dir, 'recorder.log'))

    def start_recording(self, duration):
        try:
            self.session_dir = self._create_session_dir()
            self.running = True
            self._setup_csv_file()
            self._setup_audio_file()

            self.screenshot_recorder = ScreenshotRecorder(self.data_queue, self.screenshot_freq)
            self.mouse_keyboard_recorder = MouseKeyboardRecorder(self.data_queue)
            self.audio_recorder = AudioRecorder(self.audio_file)

            self._start_recorders()
            self.save_thread = threading.Thread(target=self._save_data, daemon=True)
            self.save_thread.start()

            logging.info(f"Recording started for {duration} seconds...")
            time.sleep(duration)

            self.stop_recording()
        except Exception as e:
            logging.error(f"Error during recording: {e}")
            self.stop_recording()

    def stop_recording(self):
        logging.info("Stopping recording...")
        self.running = False
        self._stop_recorders()
        self.flush_data()
        self._close_files()
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

    def _setup_csv_file(self):
        self.csv_file = open(os.path.join(self.session_dir, "events.csv"), 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Timestamp", "EventType", "Data"])

    def _setup_audio_file(self):
        self.audio_file = wave.open(os.path.join(self.session_dir, "audio.wav"), 'wb')
        self.audio_file.setnchannels(self.config['audio_channels'])
        self.audio_file.setsampwidth(2)
        self.audio_file.setframerate(self.config['audio_samplerate'])

    def _start_recorders(self):
        self.screenshot_recorder.start()
        self.mouse_keyboard_recorder.start()
        self.audio_recorder.start()

    def _stop_recorders(self):
        self.screenshot_recorder.stop()
        self.mouse_keyboard_recorder.stop()
        self.audio_recorder.stop()

    def _close_files(self):
        if self.csv_file:
            self.csv_file.close()
        if self.audio_file:
            self.audio_file.close()

    def _save_data(self):
        buffer = []
        last_save_time = time.time()
        while self.running or not self.data_queue.empty():
            try:
                event = self.data_queue.get(timeout=0.1)
                buffer.append(event)
                if len(buffer) >= self.config['buffer_size'] or time.time() - last_save_time > self.config['buffer_time']:
                    self._process_buffer(buffer)
                    buffer = []
                    last_save_time = time.time()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error saving data: {e}")
        self._process_buffer(buffer)  # Process any remaining data

    def _process_buffer(self, buffer):
        for event_type, timestamp, data in buffer:
            self._process_event(event_type, timestamp, data)

    def _process_event(self, event_type, timestamp, data):
        try:
            if event_type == 'screenshot':
                self._save_screenshot(timestamp, data)
            elif event_type in ['mouse_move', 'mouse_click', 'mouse_scroll', 'key_press', 'key_release']:
                self._save_input_event(event_type, timestamp, data)
            else:
                logging.warning(f"Unknown event type: {event_type}")
        except Exception as e:
            logging.error(f"Error processing event {event_type}: {e}")

    def _save_screenshot(self, timestamp, data):
        filename = f"screenshot_{int(timestamp)}.png"
        img_path = os.path.join(self.session_dir, 'screenshots', filename)
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        cv2.imwrite(img_path, cv2.cvtColor(data, cv2.COLOR_RGB2BGR))
        self.csv_writer.writerow([timestamp, 'screenshot', filename])

    def _save_input_event(self, event_type, timestamp, data):
        csv_data = self._format_event_data(event_type, data)
        self.csv_writer.writerow([timestamp, event_type, csv_data])

    def _format_event_data(self, event_type, data):
        if event_type == 'mouse_move':
            return f"x={data[0]}, y={data[1]}"
        elif event_type == 'mouse_click':
            return f"x={data[0]}, y={data[1]}, button={data[2]}, pressed={data[3]}"
        elif event_type == 'mouse_scroll':
            return f"x={data[0]}, y={data[1]}, dx={data[2]}, dy={data[3]}"
        elif event_type in ['key_press', 'key_release']:
            return f"key={data}"
        else:
            return str(data)

if __name__ == "__main__":
    recorder = DatasetRecorder()
    try:
        recorder.start_recording(duration=60)  # Record for 60 seconds
    except KeyboardInterrupt:
        print("Recording stopped by user.")
    finally:
        recorder.stop_recording()

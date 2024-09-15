import os
import time
import csv
import queue
import threading
import logging
from datetime import datetime
import pyscreenshot as ImageGrab
import numpy as np
import sounddevice as sd
from pynput import mouse, keyboard
import cv2

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ScreenshotRecorder:
    def __init__(self, output_queue, frequency=10):
        self.output_queue = output_queue
        self.frequency = frequency
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._record, daemon=True).start()

    def stop(self):
        self.running = False

    def _record(self):
        while self.running:
            try:
                screenshot = ImageGrab.grab()
                self.output_queue.put(('screenshot', time.time(), np.array(screenshot)))
                time.sleep(1 / self.frequency)
            except Exception as e:
                logging.error(f"Screenshot error: {e}")

class MouseKeyboardRecorder:
    def __init__(self, output_queue):
        self.output_queue = output_queue
        self.mouse_listener = None
        self.keyboard_listener = None

    def start(self):
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll)
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release)
        self.mouse_listener.start()
        self.keyboard_listener.start()
        logging.info("Mouse and keyboard listeners started")

    def stop(self):
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        logging.info("Mouse and keyboard listeners stopped")

    def _on_move(self, x, y):
        logging.debug(f"Mouse moved to ({x}, {y})")
        self.output_queue.put(('mouse_move', time.time(), (x, y)))

    def _on_click(self, x, y, button, pressed):
        logging.debug(f"Mouse {'pressed' if pressed else 'released'} at ({x}, {y}) with {button}")
        self.output_queue.put(('mouse_click', time.time(), (x, y, str(button), pressed)))

    def _on_scroll(self, x, y, dx, dy):
        logging.debug(f"Mouse scrolled at ({x}, {y}) by ({dx}, {dy})")
        self.output_queue.put(('mouse_scroll', time.time(), (x, y, dx, dy)))

    def _on_press(self, key):
        logging.debug(f"Key pressed: {key}")
        self.output_queue.put(('key_press', time.time(), str(key)))

    def _on_release(self, key):
        logging.debug(f"Key released: {key}")
        self.output_queue.put(('key_release', time.time(), str(key)))

class AudioRecorder:
    def __init__(self, output_queue, channels=1, samplerate=44100):
        self.output_queue = output_queue
        self.channels = channels
        self.samplerate = samplerate
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._record, daemon=True).start()

    def stop(self):
        self.running = False

    def _record(self):
        def callback(indata, frames, time_info, status):
            if status:
                logging.warning(f"Audio callback status: {status}")
            if self.running:
                current_time = time.time()
                self.output_queue.put(('audio', current_time, indata.copy()))

        try:
            with sd.InputStream(callback=callback, channels=self.channels, samplerate=self.samplerate):
                logging.info("Audio recording started")
                while self.running:
                    sd.sleep(100)
        except Exception as e:
            logging.error(f"Audio recording error: {e}")
        finally:
            logging.info("Audio recording stopped")

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
        screenshot_count = 0
        audio_data = []
        last_save_time = time.time()

        while self.running or not self.data_queue.empty():
            try:
                event_type, timestamp, data = self.data_queue.get(timeout=1)
                self._process_event(event_type, timestamp, data)

                if event_type == 'screenshot':
                    screenshot_count += 1
                elif event_type == 'audio':
                    audio_data.append(data)

                # Periodic saving
                if time.time() - last_save_time > 5:  # Save every 5 seconds
                    self._save_audio_data(audio_data)
                    audio_data = []
                    last_save_time = time.time()

            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error saving data: {e}")

        # Final save
        self._save_audio_data(audio_data)

    def _process_event(self, event_type, timestamp, data):
        if event_type == 'screenshot':
            filename = f"screenshot_{int(timestamp)}.png"
            img_path = os.path.join(self.session_dir, filename)
            cv2.imwrite(img_path, cv2.cvtColor(data, cv2.COLOR_RGB2BGR))
            self.csv_writer.writerow([timestamp, event_type, filename])
            logging.debug(f"Saved screenshot: {filename}")
        elif event_type == 'audio':
            logging.debug(f"Recorded audio chunk at {timestamp}")
        else:
            self.csv_writer.writerow([timestamp, event_type, data])
            logging.debug(f"Recorded event: {event_type} at {timestamp}")

    def _save_audio_data(self, audio_data):
        if audio_data:
            try:
                audio_path = os.path.join(self.session_dir, f"audio_{int(time.time())}.npy")
                np.save(audio_path, np.concatenate(audio_data))
                logging.info(f"Saved audio data to {audio_path}")
            except Exception as e:
                logging.error(f"Error saving audio data: {e}")





if __name__ == "__main__":
    recorder = None
    try:
        recorder = DatasetRecorder(screenshot_freq=5)  # Adjust screenshot frequency as needed
        recorder.start_recording(duration=60)  # Record for 60 seconds
    except KeyboardInterrupt:
        logging.info("Recording stopped by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if recorder:
            recorder.stop_recording()
        logging.info("Recording session ended.")
        time.sleep(2)  # Allow time for final data processing

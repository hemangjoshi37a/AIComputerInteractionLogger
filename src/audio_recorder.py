import threading
import time
import logging
import sounddevice as sd
import numpy as np

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
                self.output_queue.put(('audio', time.time(), indata.copy()))

        try:
            with sd.InputStream(callback=callback, channels=self.channels, samplerate=self.samplerate):
                logging.info("Audio recording started")
                while self.running:
                    sd.sleep(100)
        except Exception as e:
            logging.error(f"Audio recording error: {e}")
        finally:
            logging.info("Audio recording stopped")

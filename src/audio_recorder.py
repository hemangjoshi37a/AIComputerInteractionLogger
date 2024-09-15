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
import wave

class AudioRecorder:
    def __init__(self, output_queue, channels=1, samplerate=44100):
        self.output_queue = output_queue
        self.channels = channels
        self.samplerate = samplerate
        self.running = False
        self.audio_buffer = []

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
                self.audio_buffer.append(indata.copy())
                if len(self.audio_buffer) >= 10:  # Save every 10 chunks
                    self.output_queue.put(('audio', time.time(), np.concatenate(self.audio_buffer)))
                    self.audio_buffer = []

        try:
            with sd.InputStream(callback=callback, channels=self.channels, samplerate=self.samplerate):
                logging.info("Audio recording started")
                while self.running:
                    sd.sleep(100)
        except Exception as e:
            logging.error(f"Audio recording error: {e}")
        finally:
            logging.info("Audio recording stopped")
            if self.audio_buffer:
                self.output_queue.put(('audio', time.time(), np.concatenate(self.audio_buffer)))


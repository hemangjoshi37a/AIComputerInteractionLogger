import threading
import logging
import sounddevice as sd
import numpy as np

class AudioRecorder:
    def __init__(self, audio_file, config):
        self.audio_file = audio_file
        self.channels = config['audio_channels']
        self.samplerate = config['audio_samplerate']
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._record, daemon=True).start()
        logging.info("Audio recorder started")

    def stop(self):
        self.running = False
        logging.info("Audio recorder stopped")

    def _record(self):
        def callback(indata, frames, time, status):
            if status:
                logging.warning(f"Audio callback status: {status}")
            if self.running:
                self.audio_file.writeframes(indata.tobytes())

        try:
            with sd.InputStream(callback=callback, channels=self.channels, samplerate=self.samplerate):
                while self.running:
                    sd.sleep(100)
        except Exception as e:
            logging.error(f"Audio recording error: {e}")

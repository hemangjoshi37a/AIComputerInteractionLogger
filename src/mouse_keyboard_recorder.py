from pynput import mouse, keyboard
import time
import logging

class MouseKeyboardRecorder:
    def __init__(self, output_queue):
        self.output_queue = output_queue
        self.mouse_listener = None
        self.keyboard_listener = None
        self.running = False

    def start(self):
        self.running = True
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
        self.running = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        logging.info("Mouse and keyboard listeners stopped")

    def is_running(self):
        return self.running and self.mouse_listener.is_alive() and self.keyboard_listener.is_alive()

    def _on_move(self, x, y):
        if self.running:
            event = ('mouse_move', time.time(), (x, y))
            self.output_queue.put(event)
            logging.debug(f"Mouse move event: {event}")

    def _on_click(self, x, y, button, pressed):
        if self.running:
            event = ('mouse_click', time.time(), (x, y, str(button), pressed))
            self.output_queue.put(event)
            logging.debug(f"Mouse click event: {event}")

    def _on_scroll(self, x, y, dx, dy):
        if self.running:
            event = ('mouse_scroll', time.time(), (x, y, dx, dy))
            self.output_queue.put(event)
            logging.debug(f"Mouse scroll event: {event}")

    def _on_press(self, key):
        if self.running:
            event = ('key_press', time.time(), str(key))
            self.output_queue.put(event)
            logging.debug(f"Key press event: {event}")

    def _on_release(self, key):
        if self.running:
            event = ('key_release', time.time(), str(key))
            self.output_queue.put(event)
            logging.debug(f"Key release event: {event}")

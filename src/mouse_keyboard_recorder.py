from pynput import mouse, keyboard
import time
import logging

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
        self.output_queue.put(('mouse_move', time.time(), (x, y)))

    def _on_click(self, x, y, button, pressed):
        self.output_queue.put(('mouse_click', time.time(), (x, y, str(button), pressed)))

    def _on_scroll(self, x, y, dx, dy):
        self.output_queue.put(('mouse_scroll', time.time(), (x, y, dx, dy)))

    def _on_press(self, key):
        self.output_queue.put(('key_press', time.time(), str(key)))

    def _on_release(self, key):
        self.output_queue.put(('key_release', time.time(), str(key)))

from pynput import mouse, keyboard
import time
import logging

class MouseKeyboardRecorder:
    def __init__(self, output_queue, config):
        self.output_queue = output_queue
        self.mouse_listener = None
        self.keyboard_listener = None
        self.running = False
        self.config = config
        self.last_mouse_move_time = 0

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
            current_time = time.time()
            if current_time - self.last_mouse_move_time >= self.config['mouse_move_throttle']:
                self.output_queue.put(('mouse_move', current_time, (x, y)))
                self.last_mouse_move_time = current_time

    def _on_click(self, x, y, button, pressed):
        if self.running:
            self.output_queue.put(('mouse_click', time.time(), (x, y, str(button), pressed)))

    def _on_scroll(self, x, y, dx, dy):
        if self.running:
            self.output_queue.put(('mouse_scroll', time.time(), (x, y, dx, dy)))

    def _on_press(self, key):
        if self.running:
            key_str = str(key)
            if key_str in self.config['mask_keys']:
                key_str = "[MASKED]"
            self.output_queue.put(('key_press', time.time(), key_str))

    def _on_release(self, key):
        if self.running:
            key_str = str(key)
            if key_str in self.config['mask_keys']:
                key_str = "[MASKED]"
            self.output_queue.put(('key_release', time.time(), key_str))

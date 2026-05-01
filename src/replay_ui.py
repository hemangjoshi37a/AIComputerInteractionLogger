import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import logging
import time


class ReplayUI:
    """Tkinter-based UI for session replay."""

    def __init__(self, session_replay, config=None):
        self.replay = session_replay
        self.config = config or {}
        self.root = None
        self.canvas = None
        self.current_image = None
        self.current_timestamp = None
        self.playback_job = None
        self.is_playing = False

        # UI settings
        self.show_mouse_cursor = self.config.get('show_mouse_cursor', True)
        self.show_keyboard_events = self.config.get('show_keyboard_events', True)
        self.show_window_info = self.config.get('show_window_info', True)
        self.window_size = self.config.get('replay_window_size', '1280x720')

    def setup_ui(self):
        """Setup the playback UI."""
        self.root = tk.Tk()
        self.root.title("Session Replay")
        self.root.geometry(self.window_size)

        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas for screenshot display
        self.canvas = tk.Canvas(main_frame, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Timeline slider
        timeline_frame = ttk.Frame(main_frame)
        timeline_frame.pack(fill=tk.X, pady=5)

        self.timeline = ttk.Scale(
            timeline_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self._on_timeline_change
        )
        self.timeline.pack(fill=tk.X)

        # Time labels
        time_frame = ttk.Frame(timeline_frame)
        time_frame.pack(fill=tk.X)

        self.current_time_label = ttk.Label(time_frame, text="00:00")
        self.current_time_label.pack(side=tk.LEFT)

        self.total_time_label = ttk.Label(time_frame, text="00:00")
        self.total_time_label.pack(side=tk.RIGHT)

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.play_button = ttk.Button(control_frame, text="Play", command=self.toggle_playback)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_playback)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.step_back_button = ttk.Button(control_frame, text="<<", command=self.step_back)
        self.step_back_button.pack(side=tk.LEFT, padx=5)

        self.step_forward_button = ttk.Button(control_frame, text=">>", command=self.step_forward)
        self.step_forward_button.pack(side=tk.LEFT, padx=5)

        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(side=tk.RIGHT, padx=5)

        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.StringVar(value="1.0x")
        speed_combo = ttk.Combobox(speed_frame, textvariable=self.speed_var, values=["0.5x", "1.0x", "2.0x", "5.0x"], width=8)
        speed_combo.pack(side=tk.LEFT, padx=5)
        speed_combo.bind("<<ComboboxSelected>>", self._on_speed_change)

        # Event info panel
        info_frame = ttk.LabelFrame(main_frame, text="Event Info")
        info_frame.pack(fill=tk.X, pady=5)

        self.event_info_text = tk.Text(info_frame, height=4, state=tk.DISABLED)
        self.event_info_text.pack(fill=tk.X, padx=5, pady=5)

        # Window info panel
        if self.show_window_info:
            window_frame = ttk.LabelFrame(main_frame, text="Window Info")
            window_frame.pack(fill=tk.X, pady=5)

            self.window_info_text = tk.Text(window_frame, height=3, state=tk.DISABLED)
            self.window_info_text.pack(fill=tk.X, padx=5, pady=5)

        # Initialize
        self._initialize_timeline()
        self._update_display()

        # Bind keyboard shortcuts
        self.root.bind('<space>', lambda e: self.toggle_playback())
        self.root.bind('<Left>', lambda e: self.step_back())
        self.root.bind('<Right>', lambda e: self.step_forward())
        self.root.bind('<Escape>', lambda e: self.root.quit())

    def _initialize_timeline(self):
        """Initialize timeline with session duration."""
        duration = self.replay.get_duration()
        self.timeline.configure(to=duration)
        self.total_time_label.config(text=self._format_time(duration))
        self.current_timestamp = self.replay.start_time

    def _format_time(self, seconds):
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def _on_timeline_change(self, value):
        """Handle timeline slider change."""
        if not self.is_playing:
            timestamp = self.replay.start_time + float(value)
            self.seek(timestamp)

    def _on_speed_change(self, event):
        """Handle speed change."""
        speed_str = self.speed_var.get()
        self.replay.playback_speed = float(speed_str.replace('x', ''))

    def _update_display(self):
        """Update the display with current frame."""
        if self.current_timestamp is None:
            return

        # Get screenshot
        screenshot = self.replay.get_screenshot(self.current_timestamp)
        if screenshot is not None:
            self._display_screenshot(screenshot)

        # Update time label
        elapsed = self.current_timestamp - self.replay.start_time
        self.current_time_label.config(text=self._format_time(elapsed))
        self.timeline.set(elapsed)

        # Update event info
        self._update_event_info()

        # Update window info
        if self.show_window_info:
            self._update_window_info()

    def _display_screenshot(self, screenshot):
        """Display screenshot on canvas."""
        # Resize to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width > 1 and canvas_height > 1:
            img_height, img_width = screenshot.shape[:2]
            scale = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            screenshot = cv2.resize(screenshot, (new_width, new_height))

        # Convert to PIL Image
        img = Image.fromarray(screenshot)
        self.current_image = ImageTk.PhotoImage(img)

        # Clear and display
        self.canvas.delete("all")
        x = (self.canvas.winfo_width() - self.current_image.width()) // 2
        y = (self.canvas.winfo_height() - self.current_image.height()) // 2
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.current_image)

    def _update_event_info(self):
        """Update event info panel."""
        events = self.replay.get_events_at_time(self.current_timestamp)

        self.event_info_text.config(state=tk.NORMAL)
        self.event_info_text.delete(1.0, tk.END)

        for event in events[-5:]:  # Show last 5 events
            event_type = event['event_type']
            data = event['data']
            self.event_info_text.insert(tk.END, f"{event_type}: {data}\n")

        self.event_info_text.config(state=tk.DISABLED)

    def _update_window_info(self):
        """Update window info panel."""
        window_changes = self.replay.get_window_changes()

        if not window_changes:
            return

        # Find most recent window change
        recent_window = None
        for change in reversed(window_changes):
            if change['timestamp'] <= self.current_timestamp:
                recent_window = change
                break

        if recent_window:
            import json
            try:
                window_info = json.loads(recent_window['data'])
                info_text = f"Title: {window_info.get('title', 'N/A')}\n"
                info_text += f"Process: {window_info.get('process_name', 'N/A')}\n"
                info_text += f"PID: {window_info.get('pid', 'N/A')}"

                self.window_info_text.config(state=tk.NORMAL)
                self.window_info_text.delete(1.0, tk.END)
                self.window_info_text.insert(tk.END, info_text)
                self.window_info_text.config(state=tk.DISABLED)
            except json.JSONDecodeError:
                pass

    def toggle_playback(self):
        """Toggle playback state."""
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()

    def start_playback(self):
        """Start playback."""
        if not self.is_playing:
            self.is_playing = True
            self.play_button.config(text="Pause")
            self._playback_loop()

    def pause_playback(self):
        """Pause playback."""
        self.is_playing = False
        self.play_button.config(text="Play")
        if self.playback_job:
            self.root.after_cancel(self.playback_job)
            self.playback_job = None

    def stop_playback(self):
        """Stop playback and reset to beginning."""
        self.pause_playback()
        self.seek(self.replay.start_time)

    def step_back(self):
        """Step back one frame."""
        if self.current_timestamp:
            step = 1.0 / self.replay.playback_speed
            new_timestamp = max(self.replay.start_time, self.current_timestamp - step)
            self.seek(new_timestamp)

    def step_forward(self):
        """Step forward one frame."""
        if self.current_timestamp:
            step = 1.0 / self.replay.playback_speed
            new_timestamp = min(self.replay.end_time, self.current_timestamp + step)
            self.seek(new_timestamp)

    def seek(self, timestamp):
        """Seek to specific timestamp."""
        self.current_timestamp = timestamp
        self._update_display()

    def _playback_loop(self):
        """Main playback loop."""
        if not self.is_playing:
            return

        # Advance time
        step = 0.1 / self.replay.playback_speed
        self.current_timestamp += step

        # Check if we've reached the end
        if self.current_timestamp >= self.replay.end_time:
            self.pause_playback()
            return

        # Update display
        self._update_display()

        # Schedule next update
        delay = int(100 / self.replay.playback_speed)
        self.playback_job = self.root.after(delay, self._playback_loop)

    def run(self):
        """Run the UI main loop."""
        if self.root:
            self.root.mainloop()

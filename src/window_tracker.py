import time
import logging
import threading
import json
import platform


class WindowTracker:
    """Tracks active window information including title, process name, and bounds."""

    def __init__(self, output_queue, config):
        self.output_queue = output_queue
        self.config = config
        self.running = False
        self.last_window_info = None
        self.polling_interval = config.get('window_poll_interval', 0.5)
        self.exclude_processes = config.get('window_exclude_processes', [])
        self.thread = None

    def start(self):
        """Start tracking window changes."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._record, daemon=True)
            self.thread.start()
            logging.info("Window tracker started")

    def stop(self):
        """Stop tracking."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logging.info("Window tracker stopped")

    def is_running(self):
        """Check if tracker is running."""
        return self.running and (self.thread is None or self.thread.is_alive())

    def _get_active_window_info(self):
        """Get current active window info."""
        try:
            system = platform.system()

            if system == "Windows":
                return self._get_windows_window_info()
            elif system == "Darwin":  # macOS
                return self._get_macos_window_info()
            elif system == "Linux":
                return self._get_linux_window_info()
            else:
                logging.warning(f"Unsupported platform: {system}")
                return None
        except Exception as e:
            logging.error(f"Error getting window info: {e}")
            return None

    def _get_windows_window_info(self):
        """Get window info on Windows."""
        try:
            import win32gui
            import win32process
            import psutil

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None

            title = win32gui.GetWindowText(hwnd)
            if not title:
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"

            if process_name in self.exclude_processes:
                return None

            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            bounds = {
                'left': left,
                'top': top,
                'width': right - left,
                'height': bottom - top
            }

            return {
                'title': title,
                'process_name': process_name,
                'pid': pid,
                'bounds': bounds
            }
        except ImportError:
            logging.warning("pywin32 not installed. Window tracking disabled.")
            return None
        except Exception as e:
            logging.error(f"Error getting Windows window info: {e}")
            return None

    def _get_macos_window_info(self):
        """Get window info on macOS."""
        try:
            from AppKit import NSWorkspace

            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if not app:
                return None

            process_name = app.localizedName()
            if process_name in self.exclude_processes:
                return None

            return {
                'title': process_name,
                'process_name': process_name,
                'pid': app.processIdentifier(),
                'bounds': {'left': 0, 'top': 0, 'width': 0, 'height': 0}
            }
        except ImportError:
            logging.warning("PyObjC not installed. Window tracking disabled.")
            return None
        except Exception as e:
            logging.error(f"Error getting macOS window info: {e}")
            return None

    def _get_linux_window_info(self):
        """Get window info on Linux."""
        try:
            import subprocess

            try:
                result = subprocess.run(
                    ['xdotool', 'getactivewindow', 'getwindowname', 'getwindowpid'],
                    capture_output=True, text=True, timeout=1
                )
                if result.returncode != 0:
                    return None

                lines = result.stdout.strip().split('\n')
                if len(lines) < 2:
                    return None

                title = lines[0]
                pid = int(lines[1]) if lines[1].isdigit() else 0

                try:
                    import psutil
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = "Unknown"

                if process_name in self.exclude_processes:
                    return None

                return {
                    'title': title,
                    'process_name': process_name,
                    'pid': pid,
                    'bounds': {'left': 0, 'top': 0, 'width': 0, 'height': 0}
                }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logging.warning("xdotool not available. Window tracking disabled.")
                return None
        except Exception as e:
            logging.error(f"Error getting Linux window info: {e}")
            return None

    def _record(self):
        """Main recording loop."""
        while self.running:
            try:
                window_info = self._get_active_window_info()

                if window_info:
                    if self.last_window_info is None or window_info != self.last_window_info:
                        self.output_queue.put(('window_change', time.time(), json.dumps(window_info)))
                        self.last_window_info = window_info
                        logging.debug(f"Window changed: {window_info['title']}")

                time.sleep(self.polling_interval)
            except Exception as e:
                logging.error(f"Error in window tracking loop: {e}")
                time.sleep(1)

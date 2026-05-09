"""Synthetic Session Simulation Engine for AI Computer Interaction Logger.

This module programmatically renders high-resolution operating system GUI canvases
and simulates natural human interaction kinetics (Bézier mouse curves, Fitts's Law,
backspace typo corrections, typing jitters, and custom idle intervals) to output
fully compliant, chronological dataset directories containing screenshots and events.csv.
"""

import os
import csv
import math
import random
import time
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont


class SyntheticSessionGenerator:
    """Enterprise-grade simulator producing high-fidelity GUI events and screenshots on-demand."""

    def __init__(self, base_output_dir: str = "dataset", width: int = 1920, height: int = 1080):
        """Initialize the synthetic session generator with specific screen dimensions and canvas bounds."""
        self.base_output_dir = base_output_dir
        self.width = width
        self.height = height
        os.makedirs(self.base_output_dir, exist_ok=True)

        # Curated harmonious color palettes for stunning premium-looking operating system UI
        self.colors = {
            "bg": "#0f172a",          # Dark slate blue background
            "card": "#1e293b",        # Sleek dark card blue
            "header": "#334155",      # Windows header border blue
            "accent": "#06b6d4",      # Neon Cyan
            "accent_glow": "#22d3ee", # Light neon cyan
            "text": "#f8fafc",        # Soft premium white
            "text_dim": "#94a3b8",    # Dim gray-blue text
            "button": "#0284c7",      # Ocean Blue button
            "button_hover": "#0369a1",# Dark ocean blue
            "red": "#ef4444",         # Red close button
            "green": "#22c55e",       # Green maximize button
            "yellow": "#eab308",      # Yellow minimize button
            "border": "#475569",      # Slate border gray
        }

    def _generate_bezier_path(self, start: Tuple[float, float], end: Tuple[float, float], steps: int = 25) -> List[Tuple[float, float]]:
        """Compute a natural organic human-like Bézier curve trajectory between two coordinates.
        
        Uses cubic Bézier interpolation with randomized control points to mimic muscle jitter
        and non-linear physical acceleration/deceleration kinematics.
        """
        x0, y0 = start
        x3, y3 = end

        # Generate control points with randomized offsets based on distance to mimic organic hand movement
        dist = math.hypot(x3 - x0, y3 - y0)
        offset_scale = dist * random.uniform(0.1, 0.4)

        x1 = x0 + (x3 - x0) * 0.25 + random.uniform(-offset_scale, offset_scale)
        y1 = y0 + (y3 - y0) * 0.25 + random.uniform(-offset_scale, offset_scale)
        x2 = x0 + (x3 - x0) * 0.75 + random.uniform(-offset_scale, offset_scale)
        y2 = y0 + (y3 - y0) * 0.75 + random.uniform(-offset_scale, offset_scale)

        path = []
        for i in range(steps):
            t = i / float(steps - 1)
            # Cubic Bezier mathematical formula
            x = (1-t)**3 * x0 + 3*(1-t)**2 * t * x1 + 3*(1-t) * t**2 * x2 + t**3 * x3
            y = (1-t)**3 * y0 + 3*(1-t)**2 * t * y1 + 3*(1-t) * t**2 * y2 + t**3 * y3
            path.append((x, y))

        return path

    def _draw_desktop_background(self, draw: ImageDraw.ImageDraw) -> None:
        """Render a beautiful, rich dark background with grid vectors and linear gradients."""
        # Draw base background color
        draw.rectangle([0, 0, self.width, self.height], fill=self.colors["bg"])

        # Render subtle cybernetic background coordinate grid lines (every 120 pixels)
        for x in range(0, self.width, 120):
            draw.line([x, 0, x, self.height], fill="#1e293b", width=1)
        for y in range(0, self.height, 120):
            draw.line([0, y, self.width, y], fill="#1e293b", width=1)

        # Draw glowing bottom taskbar
        draw.rectangle([0, self.height - 60, self.width, self.height], fill="#0b0f19")
        draw.line([0, self.height - 60, self.width, self.height - 60], fill=self.colors["border"], width=2)

        # Draw a glowing neon start button at the bottom-left
        draw.rounded_rectangle([30, self.height - 50, 150, self.height - 10], radius=6, fill=self.colors["accent"])
        draw.text((60, self.height - 38), "START", fill="#0f172a")

    def _draw_window_frame(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str) -> None:
        """Draw a premium glassmorphic window frame with minimize, maximize, and close buttons."""
        # Drop shadow effect
        draw.rounded_rectangle([x + 6, y + 6, x + w + 6, y + h + 6], radius=12, fill="#020617")

        # Main window container background
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=self.colors["card"])

        # Header bar boundary
        draw.rounded_rectangle([x, y, x + w, y + 45], radius=12, fill=self.colors["header"])
        draw.rectangle([x, y + 35, x + w, y + 45], fill=self.colors["header"])  # Flatten bottom rounded corners of header

        # Window decorative border
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, outline=self.colors["border"], width=2)

        # Header Title Text
        draw.text((x + 20, y + 14), title, fill=self.colors["text"])

        # Render close (red), minimize (yellow), and maximize (green) buttons
        draw.ellipse([x + w - 30, y + 16, x + w - 18, y + 28], fill=self.colors["red"])
        draw.ellipse([x + w - 55, y + 16, x + w - 43, y + 28], fill=self.colors["yellow"])
        draw.ellipse([x + w - 80, y + 16, x + w - 68, y + 28], fill=self.colors["green"])

    def _draw_cursor(self, img: Image.Image, x: float, y: float) -> None:
        """Render a custom high-contrast operating system cursor over the active frame buffer."""
        draw = ImageDraw.Draw(img)
        cx, cy = int(x), int(y)

        # High-precision cursor triangle polygons
        cursor_points = [
            (cx, cy),
            (cx + 18, cy + 18),
            (cx + 8, cy + 20),
            (cx + 12, cy + 30),
            (cx + 6, cy + 32),
            (cx + 2, cy + 22),
            (cx, cy)
        ]
        # Drop shadow of cursor
        shadow_points = [(p[0] + 2, p[1] + 2) for p in cursor_points]
        draw.polygon(shadow_points, fill="#020617")
        draw.polygon(cursor_points, fill=self.colors["accent"], outline=self.colors["text"], width=2)

    def _render_scene_login_form(self, draw: ImageDraw.ImageDraw, email_text: str, pass_text: str, cursor_active: str = "") -> None:
        """Render a gorgeous synthetic web login page with email and password fields."""
        wx, wy, ww, wh = 500, 200, 920, 680
        self._draw_window_frame(draw, wx, wy, ww, wh, "Chrome - Enterprise Portal Login")

        # Draw custom simulated browser URL input bar
        draw.rounded_rectangle([wx + 100, wy + 60, wx + ww - 100, wy + 95], radius=6, fill="#0f172a", outline=self.colors["border"])
        draw.text((wx + 120, wy + 70), "https://portal.enterprise.ai/login", fill=self.colors["text_dim"])

        # Render Main login card container inside the browser window
        cx, cy, cw, ch = wx + 210, wy + 140, 500, 460
        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=12, fill="#0f172a", outline=self.colors["border"], width=1)

        draw.text((cx + 150, cy + 40), "MEMBER SIGN IN", fill=self.colors["accent"])

        # Email field label and box
        draw.text((cx + 50, cy + 100), "CORPORATE EMAIL", fill=self.colors["text_dim"])
        email_border = self.colors["accent"] if cursor_active == "email" else self.colors["border"]
        draw.rounded_rectangle([cx + 50, cy + 125, cx + cw - 50, cy + 175], radius=6, fill=self.colors["card"], outline=email_border, width=2)
        draw.text((cx + 65, cy + 140), email_text, fill=self.colors["text"])

        # Password field label and box
        draw.text((cx + 50, cy + 200), "ACCESS PASSWORD", fill=self.colors["text_dim"])
        pass_border = self.colors["accent"] if cursor_active == "password" else self.colors["border"]
        draw.rounded_rectangle([cx + 50, cy + 225, cx + cw - 50, cy + 275], radius=6, fill=self.colors["card"], outline=pass_border, width=2)
        # Hide actual password letters if it's the password field
        masked_pass = "*" * len(pass_text)
        draw.text((cx + 65, cy + 240), masked_pass, fill=self.colors["text"])

        # Blue login CTA button
        btn_fill = self.colors["accent"] if cursor_active == "button" else self.colors["button"]
        draw.rounded_rectangle([cx + 50, cy + 320, cx + cw - 50, cy + 375], radius=6, fill=btn_fill)
        draw.text((cx + 200, cy + 338), "LOGIN", fill="#0f172a")

    def _render_scene_vscode_editor(self, draw: ImageDraw.ImageDraw, code_lines: List[str], current_line_idx: int) -> None:
        """Render an automated VSCode-like coding IDE environment."""
        wx, wy, ww, wh = 200, 100, 1520, 840
        self._draw_window_frame(draw, wx, wy, ww, wh, "Visual Studio Code - main.py")

        # Sidebar file structure container
        draw.rectangle([wx + 2, wy + 46, wx + 260, wy + wh - 12], fill="#0b0f19")
        draw.line([wx + 260, wy + 46, wx + 260, wy + wh - 12], fill=self.colors["border"], width=1)

        draw.text((wx + 30, wy + 80), "📁 WORKSPACE", fill=self.colors["text"])
        draw.text((wx + 50, wy + 120), "🐍 main.py", fill=self.colors["accent"])
        draw.text((wx + 50, wy + 150), "📄 config.yaml", fill=self.colors["text_dim"])
        draw.text((wx + 50, wy + 180), "📝 readme.md", fill=self.colors["text_dim"])

        # Main editor container area
        draw.rectangle([wx + 261, wy + 46, wx + ww - 2, wy + wh - 12], fill="#0f172a")

        # Top tabs navigation bar
        draw.rectangle([wx + 261, wy + 46, wx + ww - 2, wy + 85], fill="#0b0f19")
        draw.rounded_rectangle([wx + 270, wy + 52, wx + 420, wy + 85], radius=6, fill="#0f172a")
        draw.text((wx + 290, wy + 62), "🐍 main.py", fill=self.colors["accent"])
        draw.text((wx + 400, wy + 62), "×", fill=self.colors["text_dim"])

        # Render python line list onto editor window
        y_cursor = wy + 110
        for i, line in enumerate(code_lines):
            num_str = f"{i+1:2d} | "
            # Render line numbers
            draw.text((wx + 290, y_cursor), num_str, fill=self.colors["text_dim"])
            # Render actual text content
            text_color = self.colors["accent"] if i == current_line_idx else self.colors["text"]
            draw.text((wx + 340, y_cursor), line, fill=text_color)
            y_cursor += 30

    def simulate_login_scenario(self, session_id: str) -> None:
        """Execute simulation scenario generating an enterprise corporate login interaction."""
        session_path = os.path.join(self.base_output_dir, session_id)
        screenshots_path = os.path.join(session_path, "screenshots")
        os.makedirs(screenshots_path, exist_ok=True)

        events_csv = os.path.join(session_path, "events.csv")
        events_log: List[List[Any]] = []
        timestamp = time.time()

        # Visual targets relative coordinates
        email_field_pos = (500 + 210 + 250, 200 + 140 + 150)  # Center of email form field
        password_field_pos = (500 + 210 + 250, 200 + 140 + 250)  # Center of password form field
        login_btn_pos = (500 + 210 + 250, 200 + 140 + 350)  # Center of login CTA button

        current_cursor_x, current_cursor_y = 100.0, 100.0
        frame_counter = 0

        def save_current_frame(cursor_x: float, cursor_y: float, email: str, password: str, active_field: str) -> str:
            nonlocal frame_counter
            img = Image.new("RGB", (self.width, self.height))
            draw = ImageDraw.Draw(img)
            self._draw_desktop_background(draw)
            self._render_scene_login_form(draw, email, password, active_field)
            self._draw_cursor(img, cursor_x, cursor_y)

            filename = f"screenshot_{frame_counter:04d}.png"
            img.save(os.path.join(screenshots_path, filename))
            frame_counter += 1
            return filename

        # 1. Capture initial screen
        initial_file = save_current_frame(current_cursor_x, current_cursor_y, "", "", "")
        events_log.append([timestamp, "screenshot", initial_file])
        timestamp += 1.0

        # 2. Animate mouse movement path to email box
        path = self._generate_bezier_path((current_cursor_x, current_cursor_y), email_field_pos, steps=15)
        for x, y in path:
            timestamp += 0.05
            events_log.append([timestamp, "mouse_move", f"x={int(x)}, y={int(y)}"])
            current_cursor_x, current_cursor_y = x, y

        # Click inside the email input field
        timestamp += 0.1
        events_log.append([timestamp, "mouse_click", f"x={int(current_cursor_x)}, y={int(current_cursor_y)}, button=Button.left, pressed=True"])
        timestamp += 0.05
        events_log.append([timestamp, "mouse_click", f"x={int(current_cursor_x)}, y={int(current_cursor_y)}, button=Button.left, pressed=False"])
        
        click_file = save_current_frame(current_cursor_x, current_cursor_y, "", "", "email")
        events_log.append([timestamp, "screenshot", click_file])

        # 3. Simulate human typing of email with natural keystroke offset delays & small typos
        email_str = "admin@enterprise.ai"
        current_typed_email = ""
        
        # Introduce a typo that will be backspaced
        typo_seq = [("a", "a"), ("d", "ad"), ("m", "adm"), ("o", "admo"), ("\x08", "adm"), ("i", "admi"), ("n", "admin")]
        for char, current_val in typo_seq:
            timestamp += random.uniform(0.12, 0.28)
            if char == "\x08":
                events_log.append([timestamp, "key_press", "key=Key.backspace"])
            else:
                events_log.append([timestamp, "key_press", f"key='{char}'"])
            
            current_typed_email = current_val
            type_file = save_current_frame(current_cursor_x, current_cursor_y, current_typed_email, "", "email")
            events_log.append([timestamp, "screenshot", type_file])

        # Type remaining email characters
        for char in email_str[5:]:
            timestamp += random.uniform(0.1, 0.22)
            events_log.append([timestamp, "key_press", f"key='{char}'"])
            current_typed_email += char
            type_file = save_current_frame(current_cursor_x, current_cursor_y, current_typed_email, "", "email")
            events_log.append([timestamp, "screenshot", type_file])

        # 4. Animate mouse movement to password input box
        path = self._generate_bezier_path((current_cursor_x, current_cursor_y), password_field_pos, steps=12)
        for x, y in path:
            timestamp += 0.05
            events_log.append([timestamp, "mouse_move", f"x={int(x)}, y={int(y)}"])
            current_cursor_x, current_cursor_y = x, y

        # Click inside password field
        timestamp += 0.1
        events_log.append([timestamp, "mouse_click", f"x={int(current_cursor_x)}, y={int(current_cursor_y)}, button=Button.left, pressed=True"])
        timestamp += 0.05
        events_log.append([timestamp, "mouse_click", f"x={int(current_cursor_x)}, y={int(current_cursor_y)}, button=Button.left, pressed=False"])
        
        click_file = save_current_frame(current_cursor_x, current_cursor_y, current_typed_email, "", "password")
        events_log.append([timestamp, "screenshot", click_file])

        # Type password characters
        pass_str = "secret99"
        current_typed_pass = ""
        for char in pass_str:
            timestamp += random.uniform(0.08, 0.18)
            events_log.append([timestamp, "key_press", f"key='{char}'"])
            current_typed_pass += char
            type_file = save_current_frame(current_cursor_x, current_cursor_y, current_typed_email, current_typed_pass, "password")
            events_log.append([timestamp, "screenshot", type_file])

        # 5. Move mouse and click Blue LOGIN CTA Button
        path = self._generate_bezier_path((current_cursor_x, current_cursor_y), login_btn_pos, steps=15)
        for x, y in path:
            timestamp += 0.05
            events_log.append([timestamp, "mouse_move", f"x={int(x)}, y={int(y)}"])
            current_cursor_x, current_cursor_y = x, y

        # Press login button down
        timestamp += 0.1
        events_log.append([timestamp, "mouse_click", f"x={int(current_cursor_x)}, y={int(current_cursor_y)}, button=Button.left, pressed=True"])
        click_file = save_current_frame(current_cursor_x, current_cursor_y, current_typed_email, current_typed_pass, "button")
        events_log.append([timestamp, "screenshot", click_file])

        # Release login button
        timestamp += 0.08
        events_log.append([timestamp, "mouse_click", f"x={int(current_cursor_x)}, y={int(current_cursor_y)}, button=Button.left, pressed=False"])

        # Write generated data rows directly to CSV
        with open(events_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "EventType", "Data"])
            for row in events_log:
                writer.writerow(row)

    def simulate_coding_scenario(self, session_id: str) -> None:
        """Execute simulation scenario generating an automated programming IDE interaction sequence."""
        session_path = os.path.join(self.base_output_dir, session_id)
        screenshots_path = os.path.join(session_path, "screenshots")
        os.makedirs(screenshots_path, exist_ok=True)

        events_csv = os.path.join(session_path, "events.csv")
        events_log: List[List[Any]] = []
        timestamp = time.time()

        code_lines = [
            "import os",
            "import sys",
            "def main():",
            "    print('Initializing process...')",
            "    # TODO: Add logic here",
            "if __name__ == '__main__':",
            "    main()"
        ]

        current_cursor_x, current_cursor_y = 800.0, 500.0
        frame_counter = 0

        def save_current_frame(cx: float, cy: float, lines: List[str], line_idx: int) -> str:
            nonlocal frame_counter
            img = Image.new("RGB", (self.width, self.height))
            draw = ImageDraw.Draw(img)
            self._draw_desktop_background(draw)
            self._render_scene_vscode_editor(draw, lines, line_idx)
            self._draw_cursor(img, cx, cy)

            filename = f"screenshot_{frame_counter:04d}.png"
            img.save(os.path.join(screenshots_path, filename))
            frame_counter += 1
            return filename

        # Render first initial state frame
        initial_file = save_current_frame(current_cursor_x, current_cursor_y, code_lines, 0)
        events_log.append([timestamp, "screenshot", initial_file])
        timestamp += 1.0

        # Simulate user writing new line of code inside editor
        new_code_actions = [
            "    # Step 1: Check config parameter",
            "    path = os.path.join('src', 'config.json')",
            "    if os.path.exists(path):",
            "        print('Configuration loaded successfully.')"
        ]

        # Insert coding lines sequentially
        for line_to_add in new_code_actions:
            # Simulate key presses for typing each line
            for char in line_to_add:
                timestamp += random.uniform(0.06, 0.16)
                events_log.append([timestamp, "key_press", f"key='{char}'"])

            # Add completed line to list and refresh scene buffer
            code_lines.insert(4, line_to_add)
            type_file = save_current_frame(current_cursor_x, current_cursor_y, code_lines, 4)
            events_log.append([timestamp, "screenshot", type_file])
            timestamp += 0.5

        # Move mouse cursor naturally to line 3 to check print statement
        path = self._generate_bezier_path((current_cursor_x, current_cursor_y), (600.0, 250.0), steps=10)
        for x, y in path:
            timestamp += 0.05
            events_log.append([timestamp, "mouse_move", f"x={int(x)}, y={int(y)}"])
            current_cursor_x, current_cursor_y = x, y

        # Simulate click
        timestamp += 0.1
        events_log.append([timestamp, "mouse_click", f"x={int(current_cursor_x)}, y={int(current_cursor_y)}, button=Button.left, pressed=True"])
        timestamp += 0.05
        events_log.append([timestamp, "mouse_click", f"x={int(current_cursor_x)}, y={int(current_cursor_y)}, button=Button.left, pressed=False"])
        
        click_file = save_current_frame(current_cursor_x, current_cursor_y, code_lines, 3)
        events_log.append([timestamp, "screenshot", click_file])

        # Write lines to CSV
        with open(events_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "EventType", "Data"])
            for row in events_log:
                writer.writerow(row)

"""Advanced GUI Templates Library for Synthetic Operating System Interaction Simulation.

Contains comprehensive programmatic drawing logic, theme templates, and layout builders
rendering rich multi-window components (File Explorer, Settings Panel, Databases, Checkout
forms, and browser mockups) to enable diverse VLM training dataset generation.
"""

import os
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw


class GUITemplatesLibrary:
    """Enterprise programmatic UI component library drawing gorgeous visual panels with themes."""

    def __init__(self, width: int = 1920, height: int = 1080):
        """Initialize templates library with standard high-DPI canvas dimensions."""
        self.width = width
        self.height = height

        # Premium highly curated theme presets for visually stunning layouts
        self.themes = {
            "aero_dark": {
                "bg": "#0f172a",          # Deep slate background
                "card": "#1e293b",        # Core slate card blue
                "header": "#334155",      # Slate border header
                "accent": "#06b6d4",      # Neon Cyan
                "accent_glow": "#22d3ee", # Cyan glow
                "text": "#f8fafc",        # Premium white
                "text_dim": "#94a3b8",    # Slate gray text
                "border": "#475569",      # Slate gray border
                "button": "#0284c7",      # Ocean blue button
                "red": "#ef4444",
                "green": "#22c55e",
                "yellow": "#eab308"
            },
            "cyberpunk": {
                "bg": "#03001e",          # Neon dark violet background
                "card": "#120024",        # Cyberpunk purple card
                "header": "#2d004d",      # Deep neon magenta header
                "accent": "#ff007f",      # Neon Pink
                "accent_glow": "#39ff14", # Neon Green
                "text": "#ffffff",
                "text_dim": "#bcbcbc",
                "border": "#ff007f",      # Pink borders
                "button": "#730099",      # Purple CTA
                "red": "#ff0055",
                "green": "#00ffcc",
                "yellow": "#ffee00"
            },
            "pastel_cream": {
                "bg": "#fefaf6",          # Soft warm cream background
                "card": "#ffffff",        # Pure white card
                "header": "#f5e8dd",      # Gentle peach header
                "accent": "#e4a593",      # Muted rose accent
                "accent_glow": "#aad7d9", # Soft pastel teal
                "text": "#2c3e50",        # Deep navy text
                "text_dim": "#7f8c8d",    # Slate gray text
                "border": "#e8e8e8",
                "button": "#e4a593",
                "red": "#f5b7b1",
                "green": "#aed6f1",
                "yellow": "#f9e79f"
            },
            "emerald_forest": {
                "bg": "#022c22",          # Deep emerald green
                "card": "#064e3b",        # Forest card
                "header": "#047857",      # Emerald header
                "accent": "#34d399",      # Bright mint green
                "accent_glow": "#a7f3d0", # Light mint
                "text": "#f0fdf4",
                "text_dim": "#a7f3d0",
                "border": "#065f46",
                "button": "#059669",
                "red": "#f87171",
                "green": "#34d399",
                "yellow": "#fbbf24"
            }
        }

    def draw_window_shadow(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        """Render a realistic drop-shadow border around window panels."""
        draw.rounded_rectangle([x + 8, y + 8, x + w + 8, y + h + 8], radius=14, fill="#020617")

    def draw_standard_header(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str, theme: Dict[str, str]) -> None:
        """Render window header frames with close, minimize, and maximize buttons."""
        # Top header container block
        draw.rounded_rectangle([x, y, x + w, y + 45], radius=12, fill=theme["header"])
        draw.rectangle([x, y + 35, x + w, y + 45], fill=theme["header"])  # Flatten bottom rounded corners

        # Render window title text
        draw.text((x + 20, y + 14), title, fill=theme["text"])

        # Draw close, minimize, and maximize round circle buttons
        draw.ellipse([x + w - 30, y + 16, x + w - 18, y + 28], fill=theme["red"])
        draw.ellipse([x + w - 55, y + 16, x + w - 43, y + 28], fill=theme["yellow"])
        draw.ellipse([x + w - 80, y + 16, x + w - 68, y + 28], fill=theme["green"])

    def draw_scrollbar(self, draw: ImageDraw.ImageDraw, x: int, y: int, h: int, thumb_y: int, thumb_h: int, theme: Dict[str, str]) -> None:
        """Render scrollbar tracks with draggable visual slider handles."""
        # Background scroll bar track
        draw.rounded_rectangle([x, y, x + 12, y + h], radius=6, fill=theme["bg"])
        # Draggable slider handle
        draw.rounded_rectangle([x + 2, y + thumb_y, x + 10, y + thumb_y + thumb_h], radius=4, fill=theme["border"])

    def draw_checkbox(self, draw: ImageDraw.ImageDraw, x: int, y: int, checked: bool, label: str, theme: Dict[str, str]) -> None:
        """Render modern toggle checkbox selectors."""
        border_col = theme["accent"] if checked else theme["border"]
        fill_col = theme["accent"] if checked else theme["card"]

        # Check box outline
        draw.rounded_rectangle([x, y, x + 20, y + 20], radius=4, fill=fill_col, outline=border_col, width=2)
        
        # Check mark line
        if checked:
            draw.line([x + 5, y + 10, x + 9, y + 14], fill=theme["bg"], width=3)
            draw.line([x + 9, y + 14, x + 15, y + 6], fill=theme["bg"], width=3)

        # Label text
        draw.text((x + 35, y + 2), label, fill=theme["text"])

    def draw_folder_node(self, draw: ImageDraw.ImageDraw, x: int, y: int, name: str, active: bool, theme: Dict[str, str]) -> None:
        """Render hierarchical directory file nodes for file explorers."""
        folder_col = theme["accent"] if active else theme["text_dim"]
        text_col = theme["accent"] if active else theme["text"]

        # Simple polygonal drawing representing visual folders
        draw.polygon([
            (x, y + 4),
            (x + 10, y + 4),
            (x + 14, y + 10),
            (x + 30, y + 10),
            (x + 30, y + 24),
            (x, y + 24)
        ], fill=folder_col)

        draw.text((x + 40, y + 6), name, fill=text_col)

    def draw_file_grid_item(self, draw: ImageDraw.ImageDraw, x: int, y: int, name: str, icon_type: str, theme: Dict[str, str]) -> None:
        """Render standalone visual grid files (PNGs, text files, code scripts)."""
        # Outer card outline
        draw.rounded_rectangle([x, y, x + 110, y + 110], radius=8, fill=theme["bg"], outline=theme["border"])

        # Small document drawing represents visual file templates
        draw.rectangle([x + 35, y + 15, x + 75, y + 65], fill=theme["card"], outline=theme["text_dim"])
        draw.polygon([(x + 60, y + 15), (x + 75, y + 15), (x + 75, y + 30)], fill=theme["accent"])

        # Display truncated text
        truncated_name = name[:10] + "..." if len(name) > 10 else name
        draw.text((x + 15, y + 80), truncated_name, fill=theme["text"])

    def draw_settings_slider(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, ratio: float, label: str, theme: Dict[str, str]) -> None:
        """Render volumetric slider selectors for settings panels."""
        # Slider Track
        draw.rounded_rectangle([x, y + 10, x + w, y + 14], radius=2, fill=theme["border"])
        # Colored active percentage bar
        active_w = int(w * ratio)
        draw.rounded_rectangle([x, y + 10, x + active_w, y + 14], radius=2, fill=theme["accent"])

        # Draggable circle handle knob
        draw.ellipse([x + active_w - 8, y + 4, x + active_w + 8, y + 20], fill=theme["accent_glow"], outline=theme["accent"], width=2)

        # Label text
        draw.text((x, y - 18), label, fill=theme["text"])
        # Percentage numerical text
        draw.text((x + w + 15, y - 2), f"{int(ratio*100)}%", fill=theme["text_dim"])

    def draw_explorer_window(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, selected_theme: str = "aero_dark") -> None:
        """Render a gorgeous complete File Explorer interface window."""
        theme = self.themes[selected_theme]

        # Draw container box and header frame
        self.draw_window_shadow(draw, x, y, w, h)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=theme["card"], outline=theme["border"], width=2)
        self.draw_standard_header(draw, x, y, w, h, "File Explorer", theme)

        # Left folder directories navigation sidebar
        draw.rectangle([x + 2, y + 46, x + 240, y + h - 12], fill=theme["bg"])
        draw.line([x + 240, y + 46, x + 240, y + h - 12], fill=theme["border"], width=1)

        self.draw_folder_node(draw, x + 20, y + 80, "⭐ Quick Access", False, theme)
        self.draw_folder_node(draw, x + 20, y + 120, "📁 Desktop", True, theme)
        self.draw_folder_node(draw, x + 40, y + 160, "📂 Documents", False, theme)
        self.draw_folder_node(draw, x + 40, y + 200, "📂 Downloads", False, theme)
        self.draw_folder_node(draw, x + 40, y + 240, "📂 Projects", False, theme)
        self.draw_folder_node(draw, x + 20, y + 290, "💾 local_disk_C", False, theme)

        # Right grid workspace area
        grid_x = x + 270
        grid_y = y + 80
        self.draw_file_grid_item(draw, grid_x, grid_y, "main.py", "python", theme)
        self.draw_file_grid_item(draw, grid_x + 140, grid_y, "dataset.csv", "excel", theme)
        self.draw_file_grid_item(draw, grid_x + 280, grid_y, "logo.png", "image", theme)
        self.draw_file_grid_item(draw, grid_x, grid_y + 140, "readme.md", "doc", theme)
        self.draw_file_grid_item(draw, grid_x + 140, grid_y + 140, "config.yaml", "config", theme)

        # Draw right scrollbar slider
        self.draw_scrollbar(draw, x + w - 20, y + 60, h - 80, 40, 100, theme)

    def draw_settings_panel_window(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, selected_theme: str = "aero_dark") -> None:
        """Render a complete visual Control Settings configuration panel window."""
        theme = self.themes[selected_theme]

        self.draw_window_shadow(draw, x, y, w, h)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=theme["card"], outline=theme["border"], width=2)
        self.draw_standard_header(draw, x, y, w, h, "System Settings Panel", theme)

        # Left options category sidebar
        draw.rectangle([x + 2, y + 46, x + 220, y + h - 12], fill=theme["bg"])
        draw.line([x + 220, y + 46, x + 220, y + h - 12], fill=theme["border"], width=1)

        draw.text((x + 30, y + 80), "⚙️ General", fill=theme["accent"])
        draw.text((x + 30, y + 120), "🌐 Network", fill=theme["text_dim"])
        draw.text((x + 30, y + 160), "🔒 Privacy & PII", fill=theme["text_dim"])
        draw.text((x + 30, y + 200), "📈 Analytics", fill=theme["text_dim"])

        # Right content configuration sliders and checkboxes
        content_x = x + 260
        self.draw_settings_slider(draw, content_x, y + 100, 320, 0.75, "Display Screen Brightness", theme)
        self.draw_settings_slider(draw, content_x, y + 170, 320, 0.40, "Corporate Master Volume", theme)

        self.draw_checkbox(draw, content_x, y + 240, True, "Enable Optical Privacy Masking", theme)
        self.draw_checkbox(draw, content_x, y + 280, False, "Automate LLM Trajectory Summarization", theme)
        self.draw_checkbox(draw, content_x, y + 320, True, "Generate Synthetic Benchmark Datasets", theme)

        # Action Buttons
        draw.rounded_rectangle([content_x, y + 370, content_x + 140, y + 415], radius=6, fill=theme["button"])
        draw.text((content_x + 45, y + 386), "APPLY", fill=theme["text"])

        draw.rounded_rectangle([content_x + 160, y + 370, content_x + 300, y + 415], radius=6, fill=theme["card"], outline=theme["border"])
        draw.text((content_x + 205, y + 386), "CANCEL", fill=theme["text_dim"])

    def draw_shopping_checkout_window(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, selected_theme: str = "pastel_cream") -> None:
        """Render a beautiful mock checkout billing dialog form window."""
        theme = self.themes[selected_theme]

        self.draw_window_shadow(draw, x, y, w, h)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=theme["card"], outline=theme["border"], width=2)
        self.draw_standard_header(draw, x, y, w, h, "Web Checkout Billing Secure", theme)

        # Left purchase lists container
        item_x = x + 40
        draw.text((item_x, y + 80), "🛒 ORDER SUMMARY", fill=theme["accent"])

        draw.text((item_x, y + 120), "📦 Enterprise SDK Subscription (1 Year)", fill=theme["text"])
        draw.text((item_x + 400, y + 120), "$1499.00", fill=theme["text"])

        draw.text((item_x, y + 160), "☁️ Cloud Storage Hosting (10TB)", fill=theme["text"])
        draw.text((item_x + 400, y + 160), "$120.00", fill=theme["text"])

        draw.line([item_x, y + 210, item_x + 480, y + 210], fill=theme["border"], width=1)
        draw.text((item_x, y + 230), "TOTAL DUE", fill=theme["text"])
        draw.text((item_x + 400, y + 230), "$1619.00", fill=theme["accent"])

        # Right billing input card fields
        input_x = x + 560
        draw.text((input_x, y + 80), "💳 PAYMENT METHOD", fill=theme["text_dim"])

        # Cardholder name field
        draw.text((input_x, y + 110), "CARDHOLDER NAME", fill=theme["text_dim"])
        draw.rounded_rectangle([input_x, y + 130, input_x + 360, y + 170], radius=6, fill=theme["bg"], outline=theme["border"])
        draw.text((input_x + 15, y + 144), "JOHN DOE", fill=theme["text"])

        # Card number field
        draw.text((input_x, y + 190), "CREDIT CARD NUMBER", fill=theme["text_dim"])
        draw.rounded_rectangle([input_x, y + 210, input_x + 360, y + 250], radius=6, fill=theme["bg"], outline=theme["border"])
        draw.text((input_x + 15, y + 224), "4512 - 9923 - 4821 - 8802", fill=theme["text"])

        # Pay Button
        draw.rounded_rectangle([input_x, y + 280, input_x + 360, y + 330], radius=6, fill=theme["button"])
        draw.text((input_x + 120, y + 298), "PROCESS SECURE PAYMENT", fill=theme["card"])

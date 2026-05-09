"""Analytical Report Charts Renderer for AI Computer Interaction Logger.

Programmatically calculates vector layouts and coordinates to output raw SVG XML
elements (including line graphs, area fills, bar histograms, and proportional pie wedges)
with custom neon Cyberpunk and Aero styling filters from scratch.
"""

import math
from typing import List, Tuple, Dict, Any, Optional


class ReportChartsRenderer:
    """Enterprise programmatic SVG XML vector drawing engine for modern diagnostic charts."""

    def __init__(self, theme_preset: str = "cyberpunk"):
        """Initialize renderer with pre-defined cybernetic styling palettes."""
        self.themes = {
            "cyberpunk": {
                "grid": "#2d004d",
                "accent_1": "#ff007f",   # Neon Pink
                "accent_2": "#22d3ee",   # Neon Cyan
                "accent_3": "#39ff14",   # Neon Green
                "text": "#ffffff",
                "bg": "#03001e"
            },
            "aero_dark": {
                "grid": "#334155",
                "accent_1": "#0284c7",   # Ocean Blue
                "accent_2": "#06b6d4",   # Neon Cyan
                "accent_3": "#eab308",   # Yellow Accent
                "text": "#f8fafc",
                "bg": "#0f172a"
            }
        }
        self.theme = self.themes.get(theme_preset, self.themes["cyberpunk"])

    def draw_svg_line_chart(self, width: int, height: int, values: List[float], labels: List[str], title: str) -> str:
        """Render a vector line chart with glowing nodes and grid coordinate axes.
        
        Calculates viewport scaling ratios and outputs raw HTML-embeddable polyline sequences.
        """
        if not values:
            return ""

        max_val = max(values) if max(values) > 0 else 1.0
        padding_x, padding_y = 60, 50
        chart_w, chart_h = width - 2 * padding_x, height - 2 * padding_y

        # Build grid lines background
        grid_lines = ""
        for i in range(5):
            y_coord = padding_y + int(chart_h * (i / 4.0))
            grid_lines += f'<line x1="{padding_x}" y1="{y_coord}" x2="{width - padding_x}" y2="{y_coord}" stroke="{self.theme["grid"]}" stroke-dasharray="4" />'

        # Compute point coordinates
        points: List[Tuple[int, int]] = []
        for idx, val in enumerate(values):
            x = padding_x + int(chart_w * (idx / float(len(values) - 1))) if len(values) > 1 else padding_x + int(chart_w / 2)
            y = padding_y + chart_h - int(chart_h * (val / float(max_val)))
            points.append((x, y))

        # Generate polyline coordinate strings
        polyline_pts = " ".join([f"{x},{y}" for x, y in points])
        polyline_element = f'<polyline points="{polyline_pts}" fill="none" stroke="{self.theme["accent_2"]}" stroke-width="4" filter="url(#glow)" />'

        # Draw glowing data circle nodes
        nodes = ""
        for x, y in points:
            nodes += f'<circle cx="{x}" cy="{y}" r="5" fill="{self.theme["accent_1"]}" stroke="{self.theme["text"]}" stroke-width="1.5" />'

        # Compile complete SVG payload
        svg_payload = f"""<svg width="{width}" height="{height}" style="background: {self.theme["bg"]}; border-radius: 8px;">
            <defs>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="5" result="blur" />
                    <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
            </defs>
            <text x="20" y="30" fill="{self.theme["text"]}" font-family="sans-serif" font-weight="bold" font-size="16">{title}</text>
            {grid_lines}
            {polyline_element}
            {nodes}
            <line x1="{padding_x}" y1="{height - padding_y}" x2="{width - padding_x}" y2="{height - padding_y}" stroke="{self.theme["text"]}" stroke-width="2" />
        </svg>"""

        return svg_payload

    def draw_svg_bar_chart(self, width: int, height: int, categories: Dict[str, float], title: str) -> str:
        """Render a neon bar histogram comparing categories."""
        if not categories:
            return ""

        values = list(categories.values())
        keys = list(categories.keys())
        max_val = max(values) if max(values) > 0 else 1.0

        padding_x, padding_y = 60, 50
        chart_w, chart_h = width - 2 * padding_x, height - 2 * padding_y
        bar_gap = 15
        bar_w = int((chart_w - (len(values) - 1) * bar_gap) / float(len(values)))

        bars = ""
        for idx, (key, val) in enumerate(categories.items()):
            x = padding_x + idx * (bar_w + bar_gap)
            curr_bar_h = int(chart_h * (val / float(max_val)))
            y = padding_y + chart_h - curr_bar_h

            bars += f"""
            <rect x="{x}" y="{y}" width="{bar_w}" height="{curr_bar_h}" fill="{self.theme["accent_1"]}" rx="4" filter="url(#glow_pink)" />
            <text x="{x + int(bar_w/2)}" y="{y - 8}" fill="{self.theme["text"]}" font-family="sans-serif" font-size="11" text-anchor="middle">{int(val)}</text>
            <text x="{x + int(bar_w/2)}" y="{padding_y + chart_h + 18}" fill="{self.theme["text"]}" font-family="sans-serif" font-size="11" text-anchor="middle">{key}</text>
            """

        svg_payload = f"""<svg width="{width}" height="{height}" style="background: {self.theme["bg"]}; border-radius: 8px;">
            <defs>
                <filter id="glow_pink" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
            </defs>
            <text x="20" y="30" fill="{self.theme["text"]}" font-family="sans-serif" font-weight="bold" font-size="16">{title}</text>
            {bars}
            <line x1="{padding_x}" y1="{height - padding_y}" x2="{width - padding_x}" y2="{height - padding_y}" stroke="{self.theme["text"]}" stroke-width="2" />
        </svg>"""

        return svg_payload

    def draw_svg_pie_chart(self, width: int, height: int, slices: Dict[str, float], title: str) -> str:
        """Render proportional pie charts utilizing trigonometric polar math coordinates."""
        if not slices:
            return ""

        total = sum(slices.values()) if sum(slices.values()) > 0 else 1.0
        cx, cy, r = int(width / 3), int(height / 2) + 10, int(height / 3.5)

        curr_angle = 0.0
        wedges = ""
        legend = ""
        colors_list = [self.theme["accent_1"], self.theme["accent_2"], self.theme["accent_3"], "#ffee00"]

        for idx, (label, val) in enumerate(slices.items()):
            col = colors_list[idx % len(colors_list)]
            percentage = val / total
            angle_delta = percentage * 360.0

            # Calculate path segment coordinates
            x1 = cx + r * math.cos(math.radians(curr_angle))
            y1 = cy + r * math.sin(math.radians(curr_angle))
            
            next_angle = curr_angle + angle_delta
            x2 = cx + r * math.cos(math.radians(next_angle))
            y2 = cy + r * math.sin(math.radians(next_angle))

            large_arc = 1 if angle_delta > 180 else 0

            # Proportional path slice coordinates
            if angle_delta < 360:
                wedges += f'<path d="M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large_arc},1 {x2},{y2} Z" fill="{col}" filter="url(#glow_pie)" />'
            else:
                wedges += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" filter="url(#glow_pie)" />'

            # Build legend list
            leg_y = 60 + idx * 30
            legend += f"""
            <rect x="{width - 240}" y="{leg_y}" width="16" height="16" fill="{col}" rx="3" />
            <text x="{width - 210}" y="{leg_y + 13}" fill="{self.theme["text"]}" font-family="sans-serif" font-size="13">{label} ({int(val)})</text>
            """

            curr_angle = next_angle

        svg_payload = f"""<svg width="{width}" height="{height}" style="background: {self.theme["bg"]}; border-radius: 8px;">
            <defs>
                <filter id="glow_pie" x="-10%" y="-10%" width="120%" height="120%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
            </defs>
            <text x="20" y="30" fill="{self.theme["text"]}" font-family="sans-serif" font-weight="bold" font-size="16">{title}</text>
            {wedges}
            {legend}
        </svg>"""

        return svg_payload

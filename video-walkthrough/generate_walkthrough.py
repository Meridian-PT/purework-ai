#!/usr/bin/env python3
"""
PureWork Training Studio -- Video Walkthrough Pipeline

Generates a professional narrated video walkthrough by:
  1. Rendering branded scene frames with Pillow (1920x1080)
  2. Generating narration audio with edge-tts (Microsoft TTS)
  3. Compiling stills + audio into a polished MP4 with ffmpeg

Design: Feature-showcase motion graphics style -- each frame shows
a branded title card for that scene with icons and key feature text.
Looks polished and intentional for enterprise / university audiences.

When Playwright/browser support is available, run with --browser to
capture live screenshots instead.

Output: PureWork_Training_Studio_Walkthrough.mp4

Usage:
  python3 generate_walkthrough.py [--voice en-US-GuyNeural] [--skip-frames] [--skip-audio]
"""

import asyncio
import math
import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.resolve()
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
AUDIO_DIR = BASE_DIR / "audio"
SCENES_DIR = BASE_DIR / "scenes"
OUTPUT_FILE = BASE_DIR / "PureWork_Training_Studio_Walkthrough.mp4"

# ---------------------------------------------------------------------------
# Design System
# ---------------------------------------------------------------------------
# Colors matching PureWork UI dark theme
BG_PRIMARY = (15, 17, 26)        # Deep dark blue
BG_CARD = (25, 28, 42)           # Card surface
BG_SIDEBAR = (20, 22, 35)        # Sidebar
ACCENT = (99, 102, 241)          # Indigo accent
ACCENT_LIGHT = (129, 132, 255)   # Light accent
SUCCESS = (34, 197, 94)          # Green
WARNING = (250, 204, 21)         # Yellow
DANGER = (239, 68, 68)           # Red
TEXT_PRIMARY = (255, 255, 255)    # White
TEXT_SECONDARY = (165, 170, 210) # Muted text
TEXT_DIM = (100, 105, 140)       # Very muted
BORDER = (45, 48, 65)            # Border color
ORANGE = (249, 115, 22)          # Module accent
TEAL = (20, 184, 166)            # Category accent
PURPLE = (168, 85, 247)          # Quiz accent


def get_font(size, bold=False):
    """Load the best available font at the given size."""
    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for fp in paths:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def draw_gradient_bg(draw, width, height):
    """Draw a dark gradient background."""
    for y in range(height):
        t = y / height
        r = int(15 + t * 12)
        g = int(17 + t * 6)
        b = int(26 + t * 30)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def draw_top_accent(draw, width):
    """Draw an accent line at the top."""
    draw.rectangle([(0, 0), (width, 4)], fill=ACCENT)


def draw_sidebar_mockup(draw, width, height):
    """Draw a minimal sidebar mockup on the left side."""
    sidebar_w = 240
    # Sidebar background
    draw.rectangle([(0, 0), (sidebar_w, height)], fill=BG_SIDEBAR)
    # Sidebar border
    draw.line([(sidebar_w, 0), (sidebar_w, height)], fill=BORDER, width=1)

    # Logo area
    logo_font = get_font(20, bold=True)
    draw.text((20, 25), "PureWork", fill=TEXT_PRIMARY, font=logo_font)

    # Nav items
    nav_font = get_font(14)
    nav_items = [
        ("Dashboard", False),
        ("Training Studio", True),
        ("Analytics", False),
        ("Settings", False),
    ]
    y = 90
    for label, active in nav_items:
        if active:
            # Active highlight
            draw.rectangle([(8, y - 4), (sidebar_w - 8, y + 28)],
                           fill=(99, 102, 241, 30))
            draw.rectangle([(0, y - 4), (3, y + 28)], fill=ACCENT)
            draw.text((20, y), label, fill=ACCENT_LIGHT, font=nav_font)
        else:
            draw.text((20, y), label, fill=TEXT_DIM, font=nav_font)
        y += 44

    return sidebar_w


def draw_header_bar(draw, x_start, width, height, breadcrumb=""):
    """Draw a top header/toolbar area."""
    header_h = 56
    draw.rectangle([(x_start, 0), (width, header_h)], fill=BG_CARD)
    draw.line([(x_start, header_h), (width, header_h)], fill=BORDER, width=1)

    if breadcrumb:
        bc_font = get_font(14)
        draw.text((x_start + 30, 20), breadcrumb, fill=TEXT_SECONDARY, font=bc_font)

    return header_h


def draw_rounded_rect(draw, xy, radius, fill, outline=None):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    # Draw filled rounded rectangle
    draw.rectangle([(x0 + radius, y0), (x1 - radius, y1)], fill=fill)
    draw.rectangle([(x0, y0 + radius), (x1, y1 - radius)], fill=fill)
    draw.ellipse([(x0, y0), (x0 + 2*radius, y0 + 2*radius)], fill=fill)
    draw.ellipse([(x1 - 2*radius, y0), (x1, y0 + 2*radius)], fill=fill)
    draw.ellipse([(x0, y1 - 2*radius), (x0 + 2*radius, y1)], fill=fill)
    draw.ellipse([(x1 - 2*radius, y1 - 2*radius), (x1, y1)], fill=fill)
    if outline:
        # Draw outline (simplified - just rectangle outline)
        draw.rectangle([(x0 + radius, y0), (x1 - radius, y0)], fill=outline)
        draw.rectangle([(x0 + radius, y1), (x1 - radius, y1)], fill=outline)
        draw.rectangle([(x0, y0 + radius), (x0, y1 - radius)], fill=outline)
        draw.rectangle([(x1, y0 + radius), (x1, y1 - radius)], fill=outline)


def draw_course_card(draw, x, y, w, h, title, category, cat_color, modules,
                     difficulty, coming_soon=False):
    """Draw a single course card."""
    opacity = 0.4 if coming_soon else 1.0
    card_bg = BG_CARD if not coming_soon else (22, 24, 36)
    border_c = BORDER if not coming_soon else (35, 37, 48)

    # Card background
    draw_rounded_rect(draw, (x, y, x + w, y + h), 8, fill=card_bg, outline=border_c)

    # Category color bar at top
    draw.rectangle([(x, y), (x + w, y + 4)], fill=cat_color)

    # Icon area (colored circle)
    icon_cx, icon_cy = x + w // 2, y + 55
    draw.ellipse([(icon_cx - 24, icon_cy - 24), (icon_cx + 24, icon_cy + 24)],
                 fill=cat_color)
    icon_font = get_font(20, bold=True)
    abbr = title[0:2].upper()
    bbox = draw.textbbox((0, 0), abbr, font=icon_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    text_color = TEXT_PRIMARY if not coming_soon else TEXT_DIM
    draw.text((icon_cx - tw // 2, icon_cy - th // 2 - 2), abbr,
              fill=TEXT_PRIMARY, font=icon_font)

    # Title
    title_font = get_font(13, bold=True)
    # Truncate if too long
    display_title = title if len(title) <= 28 else title[:25] + "..."
    bbox_t = draw.textbbox((0, 0), display_title, font=title_font)
    tw = bbox_t[2] - bbox_t[0]
    draw.text((x + (w - tw) // 2, y + 95), display_title,
              fill=text_color, font=title_font)

    # Category pill
    cat_font = get_font(10)
    bbox_c = draw.textbbox((0, 0), category, font=cat_font)
    cw = bbox_c[2] - bbox_c[0]
    pill_x = x + (w - cw) // 2 - 6
    draw.rectangle([(pill_x, y + 120), (pill_x + cw + 12, y + 136)],
                   fill=(*cat_color, 40))
    draw.text((pill_x + 6, y + 122), category, fill=cat_color, font=cat_font)

    # Stats row
    stat_font = get_font(10)
    stats_text = f"{modules} modules  |  {difficulty}"
    bbox_s = draw.textbbox((0, 0), stats_text, font=stat_font)
    sw = bbox_s[2] - bbox_s[0]
    draw.text((x + (w - sw) // 2, y + h - 28), stats_text,
              fill=TEXT_DIM, font=stat_font)

    if coming_soon:
        cs_font = get_font(11, bold=True)
        draw.text((x + w // 2 - 40, y + h - 48), "Coming Soon",
                  fill=WARNING, font=cs_font)


def draw_feature_spotlight(draw, cx, cy, title, subtitle, icon_text, color, width=600):
    """Draw a centered feature spotlight with title, icon and description."""
    # Icon circle
    draw.ellipse([(cx - 40, cy - 40), (cx + 40, cy + 40)], fill=color)
    icon_font = get_font(28, bold=True)
    bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
    iw = bbox[2] - bbox[0]
    ih = bbox[3] - bbox[1]
    draw.text((cx - iw // 2, cy - ih // 2 - 2), icon_text,
              fill=TEXT_PRIMARY, font=icon_font)

    # Title
    title_font = get_font(36, bold=True)
    bbox_t = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox_t[2] - bbox_t[0]
    draw.text((cx - tw // 2, cy + 60), title, fill=TEXT_PRIMARY, font=title_font)

    # Subtitle (may wrap)
    sub_font = get_font(18)
    words = subtitle.split()
    lines = []
    current = ""
    for w in words:
        test = current + " " + w if current else w
        bbox_test = draw.textbbox((0, 0), test, font=sub_font)
        if bbox_test[2] - bbox_test[0] > width:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)

    y_sub = cy + 110
    for line in lines:
        bbox_l = draw.textbbox((0, 0), line, font=sub_font)
        lw = bbox_l[2] - bbox_l[0]
        draw.text((cx - lw // 2, y_sub), line, fill=TEXT_SECONDARY, font=sub_font)
        y_sub += 28


# ---------------------------------------------------------------------------
# Scene Renderers
# ---------------------------------------------------------------------------

def render_scene_login(output_path):
    """Scene 1: Login screen."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    # Center login card
    card_w, card_h = 420, 480
    cx, cy = W // 2, H // 2
    x0, y0 = cx - card_w // 2, cy - card_h // 2

    # Card background
    draw_rounded_rect(draw, (x0, y0, x0 + card_w, y0 + card_h), 12, fill=BG_CARD)

    # Card top accent
    draw.rectangle([(x0, y0), (x0 + card_w, y0 + 4)], fill=ACCENT)

    # Logo / title
    logo_font = get_font(28, bold=True)
    draw.text((cx - 80, y0 + 40), "PureWork", fill=TEXT_PRIMARY, font=logo_font)

    sub_font = get_font(14)
    draw.text((cx - 120, y0 + 80), "AI-Powered Workforce Operating System",
              fill=TEXT_SECONDARY, font=sub_font)

    # Email field
    field_y = y0 + 140
    label_font = get_font(12)
    draw.text((x0 + 30, field_y), "Email Address", fill=TEXT_SECONDARY, font=label_font)
    draw_rounded_rect(draw, (x0 + 30, field_y + 22, x0 + card_w - 30, field_y + 58),
                      6, fill=(30, 33, 50), outline=BORDER)
    input_font = get_font(14)
    draw.text((x0 + 44, field_y + 32), "admin@demo.com", fill=TEXT_DIM, font=input_font)

    # Password field
    field_y2 = field_y + 90
    draw.text((x0 + 30, field_y2), "Password", fill=TEXT_SECONDARY, font=label_font)
    draw_rounded_rect(draw, (x0 + 30, field_y2 + 22, x0 + card_w - 30, field_y2 + 58),
                      6, fill=(30, 33, 50), outline=BORDER)
    draw.text((x0 + 44, field_y2 + 32), "************", fill=TEXT_DIM, font=input_font)

    # Sign In button
    btn_y = field_y2 + 100
    draw_rounded_rect(draw, (x0 + 30, btn_y, x0 + card_w - 30, btn_y + 44),
                      8, fill=ACCENT)
    btn_font = get_font(16, bold=True)
    draw.text((cx - 25, btn_y + 12), "Sign In", fill=TEXT_PRIMARY, font=btn_font)

    # Footer
    footer_font = get_font(12)
    draw.text((cx - 70, y0 + card_h - 40), "Powered by Pure Technology",
              fill=TEXT_DIM, font=footer_font)

    img.save(str(output_path), "PNG")


def render_scene_dashboard(output_path):
    """Scene 2: Dashboard after login."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H, "Dashboard")

    content_x = sidebar_w + 40
    content_y = header_h + 40

    # Welcome message
    welcome_font = get_font(28, bold=True)
    draw.text((content_x, content_y), "Welcome back, Admin",
              fill=TEXT_PRIMARY, font=welcome_font)

    sub_font = get_font(16)
    draw.text((content_x, content_y + 40),
              "Here is your workforce overview for today.",
              fill=TEXT_SECONDARY, font=sub_font)

    # Stats cards row
    stats = [
        ("Active Courses", "12", ACCENT),
        ("Total Learners", "847", SUCCESS),
        ("Avg Completion", "78%", TEAL),
        ("Quizzes Taken", "2,341", PURPLE),
    ]
    card_w = 260
    card_h = 120
    gap = 30
    for i, (label, value, color) in enumerate(stats):
        cx = content_x + i * (card_w + gap)
        cy = content_y + 100
        draw_rounded_rect(draw, (cx, cy, cx + card_w, cy + card_h), 8,
                          fill=BG_CARD, outline=BORDER)
        draw.rectangle([(cx, cy), (cx + card_w, cy + 3)], fill=color)
        val_font = get_font(32, bold=True)
        draw.text((cx + 20, cy + 25), value, fill=TEXT_PRIMARY, font=val_font)
        lbl_font = get_font(14)
        draw.text((cx + 20, cy + 72), label, fill=TEXT_SECONDARY, font=lbl_font)

    # Quick actions area
    qa_y = content_y + 270
    qa_font = get_font(18, bold=True)
    draw.text((content_x, qa_y), "Quick Actions", fill=TEXT_PRIMARY, font=qa_font)

    actions = ["Training Studio", "Upload Content", "View Reports", "Manage Users"]
    for i, action in enumerate(actions):
        ax = content_x + i * 280
        ay = qa_y + 40
        draw_rounded_rect(draw, (ax, ay, ax + 250, ay + 60), 8,
                          fill=BG_CARD, outline=BORDER)
        act_font = get_font(14)
        draw.text((ax + 20, ay + 20), action, fill=ACCENT_LIGHT, font=act_font)

    # Recent activity
    ra_y = qa_y + 140
    draw.text((content_x, ra_y), "Recent Activity", fill=TEXT_PRIMARY, font=qa_font)
    activities = [
        "Workplace Safety course completed by 23 learners",
        "New cybersecurity training module published",
        "Quiz scores report generated for Q3",
        "3 new learners enrolled in Equipment Operation",
    ]
    act_font = get_font(13)
    for i, act in enumerate(activities):
        draw.text((content_x + 10, ra_y + 40 + i * 32), f"  {act}",
                  fill=TEXT_SECONDARY, font=act_font)
        draw.ellipse([(content_x, ra_y + 44 + i * 32),
                      (content_x + 6, ra_y + 50 + i * 32)], fill=SUCCESS)

    img.save(str(output_path), "PNG")


def render_scene_catalogue(output_path):
    """Scene 3: Course Catalogue grid."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H, "Training Studio")

    content_x = sidebar_w + 40
    content_y = header_h + 20

    # Hero area
    hero_font = get_font(24, bold=True)
    draw.text((content_x, content_y), "Course Catalogue", fill=TEXT_PRIMARY, font=hero_font)

    sub_font = get_font(14)
    draw.text((content_x, content_y + 35),
              "AI-generated training from your documentation. 12 courses available.",
              fill=TEXT_SECONDARY, font=sub_font)

    # Search bar
    search_y = content_y + 75
    search_w = 500
    draw_rounded_rect(draw, (content_x, search_y, content_x + search_w, search_y + 40),
                      6, fill=(30, 33, 50), outline=BORDER)
    draw.text((content_x + 16, search_y + 10), "Search courses...",
              fill=TEXT_DIM, font=get_font(14))

    # Category pills
    pill_x = content_x + search_w + 30
    categories = ["All", "Safety", "Operations", "Compliance", "Technical"]
    cat_colors = [ACCENT, DANGER, TEAL, WARNING, ORANGE]
    for i, (cat, color) in enumerate(zip(categories, cat_colors)):
        pw = len(cat) * 10 + 20
        is_active = i == 0
        fill_c = color if is_active else BG_CARD
        draw_rounded_rect(draw, (pill_x, search_y + 4, pill_x + pw, search_y + 36),
                          14, fill=fill_c)
        pill_font = get_font(12)
        text_c = TEXT_PRIMARY if is_active else TEXT_SECONDARY
        draw.text((pill_x + 10, search_y + 11), cat, fill=text_c, font=pill_font)
        pill_x += pw + 12

    # Course grid (3x3 + 3)
    grid_y = search_y + 60
    card_w = 290
    card_h = 175
    gap_x = 25
    gap_y = 20

    courses = [
        ("Workplace Safety", "Safety", DANGER, 4, "Beginner", False),
        ("Equipment Operation", "Operations", TEAL, 3, "Intermediate", False),
        ("Data Privacy & GDPR", "Compliance", WARNING, 5, "Advanced", False),
        ("Emergency Response", "Safety", DANGER, 3, "Beginner", False),
        ("Cybersecurity Basics", "Technical", ORANGE, 6, "Beginner", False),
        ("Quality Assurance", "Operations", TEAL, 4, "Intermediate", True),
        ("HR Compliance", "Compliance", WARNING, 3, "Beginner", True),
        ("Leadership Training", "Operations", TEAL, 5, "Advanced", True),
        ("Environmental Safety", "Safety", DANGER, 4, "Intermediate", True),
    ]

    for i, (title, cat, color, mods, diff, cs) in enumerate(courses):
        row, col = divmod(i, 3)
        if row > 2:
            break
        cx = content_x + col * (card_w + gap_x)
        cy = grid_y + row * (card_h + gap_y)
        draw_course_card(draw, cx, cy, card_w, card_h, title, cat, color,
                         mods, diff, cs)

    # Stats bar at bottom
    stats_y = H - 50
    stat_font = get_font(12)
    draw.text((content_x, stats_y), "12 courses  |  5 active  |  7 coming soon  |  38 modules total",
              fill=TEXT_DIM, font=stat_font)

    img.save(str(output_path), "PNG")


def render_scene_search(output_path):
    """Scene 4: Search & Filter with 'safety' query."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H, "Training Studio")

    content_x = sidebar_w + 40
    content_y = header_h + 20

    hero_font = get_font(24, bold=True)
    draw.text((content_x, content_y), "Course Catalogue", fill=TEXT_PRIMARY, font=hero_font)

    # Search bar with "safety" typed
    search_y = content_y + 55
    search_w = 500
    draw_rounded_rect(draw, (content_x, search_y, content_x + search_w, search_y + 40),
                      6, fill=(30, 33, 50), outline=ACCENT)
    draw.text((content_x + 16, search_y + 10), "safety",
              fill=TEXT_PRIMARY, font=get_font(14))

    # Active category pill: Safety
    pill_x = content_x + search_w + 30
    categories = ["All", "Safety", "Operations", "Compliance", "Technical"]
    cat_colors = [ACCENT, DANGER, TEAL, WARNING, ORANGE]
    for i, (cat, color) in enumerate(zip(categories, cat_colors)):
        pw = len(cat) * 10 + 20
        is_active = i == 1  # Safety is active
        fill_c = color if is_active else BG_CARD
        draw_rounded_rect(draw, (pill_x, search_y + 4, pill_x + pw, search_y + 36),
                          14, fill=fill_c)
        pill_font = get_font(12)
        text_c = TEXT_PRIMARY if is_active else TEXT_SECONDARY
        draw.text((pill_x + 10, search_y + 11), cat, fill=text_c, font=pill_font)
        pill_x += pw + 12

    # Filter results label
    filter_font = get_font(14)
    draw.text((content_x, search_y + 55),
              "Showing 3 results for \"safety\"",
              fill=ACCENT_LIGHT, font=filter_font)

    # Filtered course grid (only safety courses)
    grid_y = search_y + 90
    card_w = 290
    card_h = 175
    gap_x = 25

    safety_courses = [
        ("Workplace Safety", "Safety", DANGER, 4, "Beginner", False),
        ("Emergency Response", "Safety", DANGER, 3, "Beginner", False),
        ("Environmental Safety", "Safety", DANGER, 4, "Intermediate", True),
    ]

    for i, (title, cat, color, mods, diff, cs) in enumerate(safety_courses):
        cx = content_x + i * (card_w + gap_x)
        draw_course_card(draw, cx, grid_y, card_w, card_h, title, cat, color,
                         mods, diff, cs)

    # Highlight annotation
    anno_font = get_font(16)
    draw.text((content_x, grid_y + card_h + 40),
              "Real-time filtering as you type -- works with 10 or 10,000 courses",
              fill=TEXT_SECONDARY, font=anno_font)

    img.save(str(output_path), "PNG")


def render_scene_course_detail(output_path):
    """Scene 5: Course detail with modules list."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H,
                               "Course Catalogue  /  Workplace Safety Fundamentals")

    content_x = sidebar_w + 40
    content_y = header_h + 30

    # Course title
    title_font = get_font(28, bold=True)
    draw.text((content_x, content_y), "Workplace Safety Fundamentals",
              fill=TEXT_PRIMARY, font=title_font)

    # Category badge
    badge_font = get_font(12)
    draw_rounded_rect(draw, (content_x, content_y + 45,
                             content_x + 70, content_y + 63), 8, fill=DANGER)
    draw.text((content_x + 10, content_y + 47), "Safety", fill=TEXT_PRIMARY, font=badge_font)

    # Meta info
    meta_font = get_font(14)
    draw.text((content_x + 90, content_y + 47),
              "4 Modules  |  Beginner  |  ~2 hours  |  Last updated: Aug 2026",
              fill=TEXT_SECONDARY, font=meta_font)

    # Description
    desc_font = get_font(14)
    draw.text((content_x, content_y + 85),
              "A comprehensive introduction to workplace safety practices, covering hazard identification,",
              fill=TEXT_SECONDARY, font=desc_font)
    draw.text((content_x, content_y + 105),
              "emergency procedures, personal protective equipment, and regulatory compliance.",
              fill=TEXT_SECONDARY, font=desc_font)

    # Progress bar
    prog_y = content_y + 145
    draw.text((content_x, prog_y), "Course Progress: 25%",
              fill=TEXT_SECONDARY, font=get_font(13))
    bar_y = prog_y + 22
    draw_rounded_rect(draw, (content_x, bar_y, content_x + 800, bar_y + 8),
                      4, fill=BORDER)
    draw_rounded_rect(draw, (content_x, bar_y, content_x + 200, bar_y + 8),
                      4, fill=SUCCESS)

    # Module list
    mod_y = bar_y + 40
    module_title_font = get_font(16, bold=True)
    draw.text((content_x, mod_y), "Course Modules", fill=TEXT_PRIMARY, font=module_title_font)
    mod_y += 35

    modules = [
        ("Module 1", "Hazard Identification & Risk Assessment", True, "45 min"),
        ("Module 2", "Personal Protective Equipment (PPE)", False, "30 min"),
        ("Module 3", "Emergency Procedures & Evacuation", False, "40 min"),
        ("Module 4", "Regulatory Compliance & Reporting", False, "35 min"),
    ]

    for num, title, completed, duration in modules:
        # Module card
        draw_rounded_rect(draw, (content_x, mod_y, content_x + 900, mod_y + 70),
                          8, fill=BG_CARD, outline=BORDER)

        # Status indicator
        if completed:
            draw.ellipse([(content_x + 20, mod_y + 22),
                          (content_x + 44, mod_y + 46)], fill=SUCCESS)
            check_font = get_font(14, bold=True)
            draw.text((content_x + 27, mod_y + 24), "V", fill=TEXT_PRIMARY, font=check_font)
        else:
            draw.ellipse([(content_x + 20, mod_y + 22),
                          (content_x + 44, mod_y + 46)], outline=BORDER)

        # Title
        draw.text((content_x + 60, mod_y + 14), num,
                  fill=ACCENT_LIGHT, font=get_font(12))
        draw.text((content_x + 60, mod_y + 34), title,
                  fill=TEXT_PRIMARY, font=get_font(14))
        # Duration
        draw.text((content_x + 820, mod_y + 26), duration,
                  fill=TEXT_DIM, font=get_font(12))

        mod_y += 82

    img.save(str(output_path), "PNG")


def render_scene_ai_insights(output_path):
    """Scene 6: Module content with AI Insights panel."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H,
                               "Catalogue  /  Workplace Safety  /  Hazard Identification")

    content_x = sidebar_w + 30
    content_y = header_h + 20

    # Module title
    title_font = get_font(22, bold=True)
    draw.text((content_x, content_y), "Module 1: Hazard Identification & Risk Assessment",
              fill=TEXT_PRIMARY, font=title_font)

    # Output format tabs
    tab_y = content_y + 45
    tabs = ["Content", "Quiz", "Flashcards", "Scenarios", "Podcast",
            "Study Guide", "Summary", "Chat"]
    tab_font = get_font(11)
    tx = content_x
    for i, tab in enumerate(tabs):
        tw = len(tab) * 8 + 16
        is_active = i == 0
        fill_c = ACCENT if is_active else BG_CARD
        draw_rounded_rect(draw, (tx, tab_y, tx + tw, tab_y + 28), 4, fill=fill_c)
        draw.text((tx + 8, tab_y + 6), tab,
                  fill=TEXT_PRIMARY if is_active else TEXT_DIM, font=tab_font)
        tx += tw + 6

    # Split layout: content left, insights right
    content_area_w = 680
    insights_x = content_x + content_area_w + 30
    insights_w = W - insights_x - 30
    panel_y = tab_y + 45

    # Left: Module content excerpt
    draw_rounded_rect(draw, (content_x, panel_y,
                             content_x + content_area_w, H - 30),
                      8, fill=BG_CARD, outline=BORDER)

    body_font = get_font(13)
    content_lines = [
        "1. Introduction to Hazard Identification",
        "",
        "Hazard identification is the process of systematically",
        "finding, listing, and characterizing hazards in the",
        "workplace. This module covers the fundamental principles",
        "and practical techniques for identifying potential hazards",
        "before they lead to incidents.",
        "",
        "2. Types of Workplace Hazards",
        "",
        "  Physical: noise, vibration, radiation, temperature",
        "  Chemical: solvents, gases, dust, fumes",
        "  Biological: bacteria, viruses, mold",
        "  Ergonomic: repetitive motion, posture",
        "  Psychosocial: stress, harassment, fatigue",
        "",
        "3. Risk Assessment Framework",
        "",
        "  Step 1: Identify the hazard",
        "  Step 2: Determine who might be harmed",
        "  Step 3: Evaluate the risk level",
        "  Step 4: Implement control measures",
        "  Step 5: Record and review",
    ]
    cy = panel_y + 20
    for line in content_lines:
        if line.startswith(("1.", "2.", "3.")):
            draw.text((content_x + 20, cy), line,
                      fill=TEXT_PRIMARY, font=get_font(14, bold=True))
        else:
            draw.text((content_x + 20, cy), line,
                      fill=TEXT_SECONDARY, font=body_font)
        cy += 22

    # Right: AI Insights panel
    draw_rounded_rect(draw, (insights_x, panel_y, W - 30, H - 30),
                      8, fill=(30, 33, 50), outline=ACCENT)

    # Insights header
    draw.rectangle([(insights_x, panel_y), (W - 30, panel_y + 40)], fill=ACCENT)
    insights_title_font = get_font(14, bold=True)
    draw.text((insights_x + 15, panel_y + 10), "AI Insights",
              fill=TEXT_PRIMARY, font=insights_title_font)

    iy = panel_y + 55
    section_font = get_font(13, bold=True)
    detail_font = get_font(12)

    # Key Terms
    draw.text((insights_x + 15, iy), "Key Terms", fill=ACCENT_LIGHT, font=section_font)
    iy += 22
    terms = ["Hazard", "Risk Assessment", "PPE", "Control Hierarchy", "SDS"]
    for t in terms:
        draw_rounded_rect(draw, (insights_x + 15, iy,
                                 insights_x + 15 + len(t) * 8 + 12, iy + 22),
                          4, fill=BG_CARD)
        draw.text((insights_x + 21, iy + 3), t, fill=TEXT_SECONDARY, font=get_font(10))
        iy += 28

    # Risk Areas
    iy += 10
    draw.text((insights_x + 15, iy), "Risk Areas", fill=DANGER, font=section_font)
    iy += 25
    risks = [
        "Chemical exposure without SDS review",
        "Unguarded machinery operations",
        "Inadequate emergency egress",
    ]
    for r in risks:
        draw.text((insights_x + 25, iy), f"! {r}", fill=WARNING, font=get_font(11))
        iy += 22

    # Summary
    iy += 15
    draw.text((insights_x + 15, iy), "Summary", fill=SUCCESS, font=section_font)
    iy += 22
    summary = [
        "This module establishes the",
        "foundation for workplace safety",
        "through systematic hazard ID and",
        "risk evaluation using the 5-step",
        "framework endorsed by OSHA.",
    ]
    for line in summary:
        draw.text((insights_x + 15, iy), line, fill=TEXT_SECONDARY, font=detail_font)
        iy += 19

    img.save(str(output_path), "PNG")


def render_scene_podcast(output_path):
    """Scene 7: Podcast player with transcript."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H,
                               "Catalogue  /  Workplace Safety  /  Hazard Identification")

    content_x = sidebar_w + 30
    content_y = header_h + 20

    title_font = get_font(22, bold=True)
    draw.text((content_x, content_y), "Module 1: Hazard Identification & Risk Assessment",
              fill=TEXT_PRIMARY, font=title_font)

    # Tab bar with Podcast active
    tab_y = content_y + 45
    tabs = ["Content", "Quiz", "Flashcards", "Scenarios", "Podcast",
            "Study Guide", "Summary", "Chat"]
    tab_font = get_font(11)
    tx = content_x
    for i, tab in enumerate(tabs):
        tw = len(tab) * 8 + 16
        is_active = i == 4  # Podcast
        fill_c = ACCENT if is_active else BG_CARD
        draw_rounded_rect(draw, (tx, tab_y, tx + tw, tab_y + 28), 4, fill=fill_c)
        draw.text((tx + 8, tab_y + 6), tab,
                  fill=TEXT_PRIMARY if is_active else TEXT_DIM, font=tab_font)
        tx += tw + 6

    panel_y = tab_y + 50

    # Podcast player card
    player_w = W - content_x - 60
    draw_rounded_rect(draw, (content_x, panel_y, content_x + player_w, panel_y + 120),
                      8, fill=BG_CARD, outline=BORDER)

    # Play button
    play_cx = content_x + 50
    play_cy = panel_y + 60
    draw.ellipse([(play_cx - 28, play_cy - 28), (play_cx + 28, play_cy + 28)],
                 fill=ACCENT)
    # Triangle play icon
    draw.polygon([(play_cx - 8, play_cy - 14), (play_cx - 8, play_cy + 14),
                  (play_cx + 14, play_cy)], fill=TEXT_PRIMARY)

    # Track info
    draw.text((content_x + 100, panel_y + 20), "Audio Overview: Hazard Identification",
              fill=TEXT_PRIMARY, font=get_font(16, bold=True))
    draw.text((content_x + 100, panel_y + 48), "Two-host AI-generated podcast discussion",
              fill=TEXT_SECONDARY, font=get_font(13))

    # Progress bar
    prog_y = panel_y + 80
    draw_rounded_rect(draw, (content_x + 100, prog_y,
                             content_x + player_w - 180, prog_y + 6),
                      3, fill=BORDER)
    draw_rounded_rect(draw, (content_x + 100, prog_y,
                             content_x + 450, prog_y + 6),
                      3, fill=ACCENT)
    draw.text((content_x + player_w - 170, prog_y - 6), "3:42 / 8:15",
              fill=TEXT_DIM, font=get_font(12))

    # TTS badge
    draw.text((content_x + player_w - 80, panel_y + 20), "Voice Active",
              fill=SUCCESS, font=get_font(11, bold=True))

    # Transcript area
    trans_y = panel_y + 140
    draw.text((content_x, trans_y), "Transcript", fill=TEXT_PRIMARY,
              font=get_font(16, bold=True))

    trans_y += 35
    transcript_lines = [
        ("Host 1:", "Welcome to this audio overview on Hazard Identification.", ACCENT_LIGHT),
        ("", "Today we are going to break down the essentials of", TEXT_SECONDARY),
        ("", "identifying and assessing workplace hazards.", TEXT_SECONDARY),
        ("", "", TEXT_SECONDARY),
        ("Host 2:", "That is right. And what is fascinating is that most", ORANGE),
        ("", "workplace incidents are completely preventable when", TEXT_SECONDARY),
        ("", "you follow a systematic hazard identification process.", TEXT_SECONDARY),
        ("", "", TEXT_SECONDARY),
        ("Host 1:", "Let us start with the five categories of workplace", ACCENT_LIGHT),
        ("", "hazards. The first is physical hazards...", TEXT_SECONDARY),
        ("", "", TEXT_SECONDARY),
        ("Host 2:", "Right -- noise, vibration, radiation, and extreme", ORANGE),
        ("", "temperatures. These are often the most obvious but", TEXT_SECONDARY),
        ("", "still frequently overlooked in routine inspections.", TEXT_SECONDARY),
        ("", "", TEXT_SECONDARY),
        ("Host 1:", "Exactly. And the second category, chemical hazards,", ACCENT_LIGHT),
        ("", "requires understanding Safety Data Sheets, or SDS.", TEXT_SECONDARY),
    ]

    trans_font = get_font(13)
    host_font = get_font(13, bold=True)
    for host, text, color in transcript_lines:
        if host:
            draw.text((content_x + 10, trans_y), host, fill=color, font=host_font)
            draw.text((content_x + 80, trans_y), text, fill=TEXT_SECONDARY, font=trans_font)
        else:
            draw.text((content_x + 80, trans_y), text, fill=TEXT_SECONDARY, font=trans_font)
        trans_y += 22

    img.save(str(output_path), "PNG")


def render_scene_chat(output_path):
    """Scene 8: Document Chat."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H,
                               "Catalogue  /  Workplace Safety  /  Hazard Identification")

    content_x = sidebar_w + 30
    content_y = header_h + 20

    title_font = get_font(22, bold=True)
    draw.text((content_x, content_y), "Module 1: Hazard Identification & Risk Assessment",
              fill=TEXT_PRIMARY, font=title_font)

    # Tab bar with Chat active
    tab_y = content_y + 45
    tabs = ["Content", "Quiz", "Flashcards", "Scenarios", "Podcast",
            "Study Guide", "Summary", "Chat"]
    tab_font = get_font(11)
    tx = content_x
    for i, tab in enumerate(tabs):
        tw = len(tab) * 8 + 16
        is_active = i == 7  # Chat
        fill_c = ACCENT if is_active else BG_CARD
        draw_rounded_rect(draw, (tx, tab_y, tx + tw, tab_y + 28), 4, fill=fill_c)
        draw.text((tx + 8, tab_y + 6), tab,
                  fill=TEXT_PRIMARY if is_active else TEXT_DIM, font=tab_font)
        tx += tw + 6

    panel_y = tab_y + 50
    chat_w = W - content_x - 60

    # Chat area
    draw_rounded_rect(draw, (content_x, panel_y, content_x + chat_w, H - 80),
                      8, fill=BG_CARD, outline=BORDER)

    # Chat header
    draw.rectangle([(content_x, panel_y), (content_x + chat_w, panel_y + 40)],
                   fill=(30, 33, 50))
    draw.text((content_x + 15, panel_y + 10), "Document Chat -- Ask about this module",
              fill=TEXT_PRIMARY, font=get_font(14, bold=True))

    # Chat messages
    cy = panel_y + 60
    chat_font = get_font(13)

    # User message
    user_msg = "What are the five categories of workplace hazards?"
    msg_w = len(user_msg) * 8 + 30
    msg_x = content_x + chat_w - msg_w - 20
    draw_rounded_rect(draw, (msg_x, cy, msg_x + msg_w, cy + 36),
                      8, fill=ACCENT)
    draw.text((msg_x + 15, cy + 8), user_msg, fill=TEXT_PRIMARY, font=chat_font)

    # AI response
    cy += 60
    ai_lines = [
        "The five categories of workplace hazards covered in this",
        "module are:",
        "",
        "1. Physical - noise, vibration, radiation, temperature",
        "2. Chemical - solvents, gases, dust, fumes",
        "3. Biological - bacteria, viruses, mold",
        "4. Ergonomic - repetitive motion, poor posture",
        "5. Psychosocial - stress, harassment, fatigue",
        "",
        "Each category requires different identification methods and",
        "control measures, which are detailed in Section 2 of this module.",
    ]
    resp_w = 600
    draw_rounded_rect(draw, (content_x + 20, cy,
                             content_x + 20 + resp_w, cy + len(ai_lines) * 22 + 20),
                      8, fill=(30, 33, 50))

    # AI avatar
    draw.ellipse([(content_x + 24, cy + 4), (content_x + 44, cy + 24)],
                 fill=ACCENT)
    draw.text((content_x + 30, cy + 5), "M", fill=TEXT_PRIMARY, font=get_font(11, bold=True))

    for i, line in enumerate(ai_lines):
        draw.text((content_x + 35, cy + 10 + i * 22), line,
                  fill=TEXT_SECONDARY, font=chat_font)

    # Input area
    input_y = H - 75
    draw_rounded_rect(draw, (content_x + 10, input_y,
                             content_x + chat_w - 10, input_y + 40),
                      6, fill=(30, 33, 50), outline=BORDER)
    draw.text((content_x + 25, input_y + 10),
              "Ask a question about this module...",
              fill=TEXT_DIM, font=get_font(13))

    img.save(str(output_path), "PNG")


def render_scene_studyguide(output_path):
    """Scene 9: Study Guide view."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H,
                               "Catalogue  /  Workplace Safety  /  Hazard Identification")

    content_x = sidebar_w + 30
    content_y = header_h + 20

    title_font = get_font(22, bold=True)
    draw.text((content_x, content_y), "Module 1: Hazard Identification & Risk Assessment",
              fill=TEXT_PRIMARY, font=title_font)

    # Tab bar with Study Guide active
    tab_y = content_y + 45
    tabs = ["Content", "Quiz", "Flashcards", "Scenarios", "Podcast",
            "Study Guide", "Summary", "Chat"]
    tab_font = get_font(11)
    tx = content_x
    for i, tab in enumerate(tabs):
        tw = len(tab) * 8 + 16
        is_active = i == 5  # Study Guide
        fill_c = ACCENT if is_active else BG_CARD
        draw_rounded_rect(draw, (tx, tab_y, tx + tw, tab_y + 28), 4, fill=fill_c)
        draw.text((tx + 8, tab_y + 6), tab,
                  fill=TEXT_PRIMARY if is_active else TEXT_DIM, font=tab_font)
        tx += tw + 6

    panel_y = tab_y + 50

    # Three columns: Study Guide, Scenario Builder, Flashcards
    col_w = (W - content_x - 80) // 3
    col_gap = 20

    # Column 1: Study Guide
    c1x = content_x
    draw_rounded_rect(draw, (c1x, panel_y, c1x + col_w, H - 40),
                      8, fill=BG_CARD, outline=BORDER)
    draw.rectangle([(c1x, panel_y), (c1x + col_w, panel_y + 36)], fill=SUCCESS)
    draw.text((c1x + 15, panel_y + 8), "Study Guide",
              fill=TEXT_PRIMARY, font=get_font(14, bold=True))

    sg_items = [
        ("Learning Objectives", [
            "Identify 5 hazard categories",
            "Apply risk assessment framework",
            "Select appropriate controls",
        ]),
        ("Key Concepts", [
            "Hierarchy of Controls",
            "Safety Data Sheets (SDS)",
            "OSHA compliance requirements",
        ]),
        ("Review Questions", [
            "What is the first step in risk assessment?",
            "Name three types of PPE",
            "When should an SDS be consulted?",
        ]),
    ]
    sy = panel_y + 50
    for section, items in sg_items:
        draw.text((c1x + 15, sy), section, fill=ACCENT_LIGHT, font=get_font(13, bold=True))
        sy += 22
        for item in items:
            draw.text((c1x + 25, sy), f"  {item}", fill=TEXT_SECONDARY, font=get_font(11))
            sy += 20
        sy += 12

    # Column 2: Scenario Builder
    c2x = c1x + col_w + col_gap
    draw_rounded_rect(draw, (c2x, panel_y, c2x + col_w, H - 40),
                      8, fill=BG_CARD, outline=BORDER)
    draw.rectangle([(c2x, panel_y), (c2x + col_w, panel_y + 36)], fill=ORANGE)
    draw.text((c2x + 15, panel_y + 8), "Scenario Builder",
              fill=TEXT_PRIMARY, font=get_font(14, bold=True))

    scenario = [
        "Scenario: Chemical Spill Response",
        "",
        "You are a shift supervisor at a",
        "manufacturing facility. A worker",
        "reports a chemical spill near the",
        "loading dock. The substance is",
        "unidentified.",
        "",
        "What steps would you take?",
        "",
        "A) Evacuate the area immediately",
        "B) Identify the chemical via SDS",
        "C) Attempt to contain the spill",
        "D) Contact emergency services",
        "",
        "Consider: Which steps can be",
        "performed simultaneously? What is",
        "the correct priority order?",
    ]
    sy = panel_y + 50
    for line in scenario:
        font = get_font(12, bold=True) if line.startswith("Scenario:") else get_font(11)
        color = TEXT_PRIMARY if line.startswith(("A)", "B)", "C)", "D)")) else TEXT_SECONDARY
        draw.text((c2x + 15, sy), line, fill=color, font=font)
        sy += 20

    # Column 3: Flashcards
    c3x = c2x + col_w + col_gap
    draw_rounded_rect(draw, (c3x, panel_y, c3x + col_w, H - 40),
                      8, fill=BG_CARD, outline=BORDER)
    draw.rectangle([(c3x, panel_y), (c3x + col_w, panel_y + 36)], fill=PURPLE)
    draw.text((c3x + 15, panel_y + 8), "Flashcards",
              fill=TEXT_PRIMARY, font=get_font(14, bold=True))

    # Flashcard
    fc_y = panel_y + 60
    draw_rounded_rect(draw, (c3x + 15, fc_y, c3x + col_w - 15, fc_y + 200),
                      8, fill=(35, 38, 55), outline=ACCENT)
    draw.text((c3x + 30, fc_y + 20), "Card 3 of 15",
              fill=TEXT_DIM, font=get_font(10))
    draw.text((c3x + 30, fc_y + 50), "What is the",
              fill=TEXT_PRIMARY, font=get_font(18, bold=True))
    draw.text((c3x + 30, fc_y + 80), "Hierarchy of Controls?",
              fill=TEXT_PRIMARY, font=get_font(18, bold=True))
    draw.text((c3x + 30, fc_y + 130), "Tap to reveal answer",
              fill=ACCENT_LIGHT, font=get_font(13))

    # Navigation dots
    dot_y = fc_y + 220
    for i in range(5):
        color = ACCENT if i == 2 else BORDER
        draw.ellipse([(c3x + col_w // 2 - 30 + i * 14, dot_y),
                      (c3x + col_w // 2 - 22 + i * 14, dot_y + 8)], fill=color)

    img.save(str(output_path), "PNG")


def render_scene_quiz(output_path):
    """Scene 10: Quiz view."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H,
                               "Catalogue  /  Workplace Safety  /  Hazard Identification")

    content_x = sidebar_w + 30
    content_y = header_h + 20

    title_font = get_font(22, bold=True)
    draw.text((content_x, content_y), "Module 1: Hazard Identification & Risk Assessment",
              fill=TEXT_PRIMARY, font=title_font)

    # Tab bar with Quiz active
    tab_y = content_y + 45
    tabs = ["Content", "Quiz", "Flashcards", "Scenarios", "Podcast",
            "Study Guide", "Summary", "Chat"]
    tab_font = get_font(11)
    tx = content_x
    for i, tab in enumerate(tabs):
        tw = len(tab) * 8 + 16
        is_active = i == 1  # Quiz
        fill_c = ACCENT if is_active else BG_CARD
        draw_rounded_rect(draw, (tx, tab_y, tx + tw, tab_y + 28), 4, fill=fill_c)
        draw.text((tx + 8, tab_y + 6), tab,
                  fill=TEXT_PRIMARY if is_active else TEXT_DIM, font=tab_font)
        tx += tw + 6

    panel_y = tab_y + 50

    # Quiz card
    quiz_w = W - content_x - 60
    draw_rounded_rect(draw, (content_x, panel_y, content_x + quiz_w, H - 40),
                      8, fill=BG_CARD, outline=BORDER)

    # Quiz header
    draw.rectangle([(content_x, panel_y), (content_x + quiz_w, panel_y + 44)],
                   fill=(30, 33, 50))
    draw.text((content_x + 20, panel_y + 12),
              "Knowledge Assessment  |  Question 3 of 10",
              fill=TEXT_PRIMARY, font=get_font(14, bold=True))

    # Progress dots
    dot_x = content_x + quiz_w - 200
    for i in range(10):
        if i < 2:
            color = SUCCESS  # Correct
        elif i == 2:
            color = ACCENT  # Current
        else:
            color = BORDER  # Not answered
        draw.ellipse([(dot_x + i * 18, panel_y + 16),
                      (dot_x + i * 18 + 10, panel_y + 26)], fill=color)

    # Question
    qy = panel_y + 70
    q_font = get_font(18)
    draw.text((content_x + 30, qy),
              "Which of the following is NOT one of the five categories of",
              fill=TEXT_PRIMARY, font=q_font)
    draw.text((content_x + 30, qy + 28),
              "workplace hazards discussed in this module?",
              fill=TEXT_PRIMARY, font=q_font)

    # Answer options
    answers = [
        ("A", "Physical hazards (noise, vibration, radiation)", False, False),
        ("B", "Financial hazards (budget overruns, cost risks)", False, True),
        ("C", "Chemical hazards (solvents, gases, dust)", True, False),
        ("D", "Psychosocial hazards (stress, harassment)", False, False),
    ]

    ay = qy + 80
    for letter, text, selected, correct_answer in answers:
        option_h = 50
        if selected:
            border = ACCENT
            fill = (35, 38, 60)
        else:
            border = BORDER
            fill = BG_CARD

        draw_rounded_rect(draw, (content_x + 30, ay,
                                 content_x + quiz_w - 30, ay + option_h),
                          8, fill=fill, outline=border)

        # Letter circle
        draw.ellipse([(content_x + 45, ay + 12),
                      (content_x + 73, ay + 40)],
                     fill=ACCENT if selected else BORDER)
        draw.text((content_x + 53, ay + 15), letter,
                  fill=TEXT_PRIMARY, font=get_font(14, bold=True))

        # Text
        draw.text((content_x + 85, ay + 15), text,
                  fill=TEXT_PRIMARY, font=get_font(14))

        ay += option_h + 12

    # Submit button
    btn_y = ay + 20
    draw_rounded_rect(draw, (content_x + 30, btn_y,
                             content_x + 180, btn_y + 42),
                      8, fill=ACCENT)
    draw.text((content_x + 60, btn_y + 10), "Submit Answer",
              fill=TEXT_PRIMARY, font=get_font(14, bold=True))

    # Score display
    draw.text((content_x + quiz_w - 200, btn_y + 10),
              "Score so far: 2/2 (100%)",
              fill=SUCCESS, font=get_font(14, bold=True))

    img.save(str(output_path), "PNG")


def render_scene_back_catalogue(output_path):
    """Scene 11: Back to catalogue (same as scene 3 but with progress indicators)."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(draw, W, H)

    sidebar_w = draw_sidebar_mockup(draw, W, H)
    header_h = draw_header_bar(draw, sidebar_w, W, H, "Training Studio")

    content_x = sidebar_w + 40
    content_y = header_h + 20

    hero_font = get_font(24, bold=True)
    draw.text((content_x, content_y), "Course Catalogue", fill=TEXT_PRIMARY, font=hero_font)

    sub_font = get_font(14)
    draw.text((content_x, content_y + 35),
              "The complete learning journey -- catalogue to course to module to assessment.",
              fill=TEXT_SECONDARY, font=sub_font)

    # Search bar
    search_y = content_y + 75
    search_w = 500
    draw_rounded_rect(draw, (content_x, search_y, content_x + search_w, search_y + 40),
                      6, fill=(30, 33, 50), outline=BORDER)
    draw.text((content_x + 16, search_y + 10), "Search courses...",
              fill=TEXT_DIM, font=get_font(14))

    # Category pills (All active)
    pill_x = content_x + search_w + 30
    categories = ["All", "Safety", "Operations", "Compliance", "Technical"]
    cat_colors = [ACCENT, DANGER, TEAL, WARNING, ORANGE]
    for i, (cat, color) in enumerate(zip(categories, cat_colors)):
        pw = len(cat) * 10 + 20
        is_active = i == 0
        fill_c = color if is_active else BG_CARD
        draw_rounded_rect(draw, (pill_x, search_y + 4, pill_x + pw, search_y + 36),
                          14, fill=fill_c)
        pill_font = get_font(12)
        text_c = TEXT_PRIMARY if is_active else TEXT_SECONDARY
        draw.text((pill_x + 10, search_y + 11), cat, fill=text_c, font=pill_font)
        pill_x += pw + 12

    # Course grid with progress bars
    grid_y = search_y + 60
    card_w = 290
    card_h = 190
    gap_x = 25
    gap_y = 20

    courses = [
        ("Workplace Safety", "Safety", DANGER, 4, "Beginner", False, 0.25),
        ("Equipment Operation", "Operations", TEAL, 3, "Intermediate", False, 0.0),
        ("Data Privacy & GDPR", "Compliance", WARNING, 5, "Advanced", False, 0.6),
        ("Emergency Response", "Safety", DANGER, 3, "Beginner", False, 0.0),
        ("Cybersecurity Basics", "Technical", ORANGE, 6, "Beginner", False, 1.0),
        ("Quality Assurance", "Operations", TEAL, 4, "Intermediate", True, 0.0),
        ("HR Compliance", "Compliance", WARNING, 3, "Beginner", True, 0.0),
        ("Leadership Training", "Operations", TEAL, 5, "Advanced", True, 0.0),
        ("Environmental Safety", "Safety", DANGER, 4, "Intermediate", True, 0.0),
    ]

    for i, (title, cat, color, mods, diff, cs, progress) in enumerate(courses):
        row, col = divmod(i, 3)
        if row > 2:
            break
        cx = content_x + col * (card_w + gap_x)
        cy = grid_y + row * (card_h + gap_y)
        draw_course_card(draw, cx, cy, card_w, card_h - 15, title, cat, color,
                         mods, diff, cs)
        # Add progress bar below card
        if not cs and progress > 0:
            bar_y = cy + card_h - 12
            draw_rounded_rect(draw, (cx + 10, bar_y, cx + card_w - 10, bar_y + 6),
                              3, fill=BORDER)
            bar_w = int((card_w - 20) * progress)
            if bar_w > 0:
                bar_color = SUCCESS if progress >= 1.0 else ACCENT
                draw_rounded_rect(draw, (cx + 10, bar_y, cx + 10 + bar_w, bar_y + 6),
                                  3, fill=bar_color)

    # Summary text
    summary_y = H - 60
    draw.text((content_x, summary_y),
              "12 courses  |  5 active  |  7 coming soon  |  38 modules  |  AI-generated from your content",
              fill=TEXT_DIM, font=get_font(13))

    img.save(str(output_path), "PNG")


def render_scene_closing(output_path):
    """Scene 12: Closing title card."""
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG_PRIMARY)
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(H):
        t = y / H
        r = int(15 + t * 15)
        g = int(17 + t * 5)
        b = int(26 + t * 40)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Accent line at top
    draw.rectangle([(0, 0), (W, 4)], fill=ACCENT)

    # Large icon
    cx = W // 2
    draw.ellipse([(cx - 50, 260), (cx + 50, 360)], fill=ACCENT)
    icon_font = get_font(36, bold=True)
    draw.text((cx - 22, 285), "PW", fill=TEXT_PRIMARY, font=icon_font)

    # Main title
    title_font = get_font(72, bold=True)
    title_text = "PureWork Training Studio"
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, 400), title_text, fill=TEXT_PRIMARY, font=title_font)

    # Subtitle
    subtitle_font = get_font(36)
    subtitle_text = "Enterprise Training, Powered by AI"
    bbox2 = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    sw = bbox2[2] - bbox2[0]
    draw.text(((W - sw) / 2, 500), subtitle_text, fill=TEXT_SECONDARY, font=subtitle_font)

    # Accent divider
    div_y = 570
    div_w = 200
    draw.rectangle([((W - div_w) / 2, div_y), ((W + div_w) / 2, div_y + 3)],
                    fill=ACCENT)

    # URL
    url_font = get_font(32)
    url_text = "purebrain.ai"
    bbox3 = draw.textbbox((0, 0), url_text, font=url_font)
    uw = bbox3[2] - bbox3[0]
    draw.text(((W - uw) / 2, 610), url_text, fill=ACCENT, font=url_font)

    # Features list
    features = [
        "AI-Generated Courses from Your Documents",
        "Interactive Quizzes & Assessments",
        "Two-Voice Podcast Overviews",
        "Document Chat & Study Guides",
    ]
    feat_font = get_font(18)
    fy = 690
    for feat in features:
        bbox_f = draw.textbbox((0, 0), feat, font=feat_font)
        fw = bbox_f[2] - bbox_f[0]
        draw.text(((W - fw) / 2, fy), feat, fill=TEXT_SECONDARY, font=feat_font)
        fy += 32

    # Footer
    footer_font = get_font(18)
    footer_text = "Pure Technology  |  Reimagining Data Innovation"
    bbox4 = draw.textbbox((0, 0), footer_text, font=footer_font)
    fw = bbox4[2] - bbox4[0]
    draw.text(((W - fw) / 2, 940), footer_text, fill=TEXT_DIM, font=footer_font)

    img.save(str(output_path), "PNG")


# ---------------------------------------------------------------------------
# Scene Definitions (with renderers)
# ---------------------------------------------------------------------------
SCENES = [
    {
        "id": "01_login",
        "name": "Login Screen",
        "screenshot": "01_login.png",
        "narration": (
            "Welcome to PureWork Training Studio, "
            "an enterprise-grade learning management system powered by artificial intelligence."
        ),
        "duration": 6,
        "renderer": render_scene_login,
    },
    {
        "id": "02_dashboard",
        "name": "Dashboard",
        "screenshot": "02_dashboard.png",
        "narration": (
            "After signing in, administrators see the main dashboard "
            "with quick access to all platform features."
        ),
        "duration": 6,
        "renderer": render_scene_dashboard,
    },
    {
        "id": "03_catalogue",
        "name": "Course Catalogue",
        "screenshot": "03_catalogue.png",
        "narration": (
            "The course catalogue organizes all training content into a searchable, filterable grid. "
            "Each course is AI-generated from your existing documentation."
        ),
        "duration": 8,
        "renderer": render_scene_catalogue,
    },
    {
        "id": "04_search",
        "name": "Search & Filter",
        "screenshot": "04_search.png",
        "narration": (
            "Real-time search and category filters help learners find exactly what they need, "
            "whether you have ten courses or ten thousand."
        ),
        "duration": 7,
        "renderer": render_scene_search,
    },
    {
        "id": "05_course_detail",
        "name": "Course Detail",
        "screenshot": "05_course_detail.png",
        "narration": (
            "Inside each course, structured modules guide learners through the material "
            "with clear objectives and progress tracking."
        ),
        "duration": 7,
        "renderer": render_scene_course_detail,
    },
    {
        "id": "06_ai_insights",
        "name": "Module Content with AI Insights",
        "screenshot": "06_ai_insights.png",
        "narration": (
            "Every module includes an AI-generated insights panel with key terms, "
            "risk areas, and a comprehensive summary."
        ),
        "duration": 8,
        "renderer": render_scene_ai_insights,
    },
    {
        "id": "07_podcast",
        "name": "Podcast Player",
        "screenshot": "07_podcast.png",
        "narration": (
            "The audio overview brings content to life as an AI-generated podcast "
            "with two distinct voices, complete with a synchronized transcript."
        ),
        "duration": 8,
        "renderer": render_scene_podcast,
    },
    {
        "id": "08_chat",
        "name": "Document Chat",
        "screenshot": "08_chat.png",
        "narration": (
            "Document Chat lets learners ask questions about the course material "
            "and receive instant, contextual answers."
        ),
        "duration": 7,
        "renderer": render_scene_chat,
    },
    {
        "id": "09_studyguide",
        "name": "Study Guide",
        "screenshot": "09_studyguide.png",
        "narration": (
            "AI-generated study guides, real-world scenario builders, and flashcards "
            "transform passive reading into active learning."
        ),
        "duration": 7,
        "renderer": render_scene_studyguide,
    },
    {
        "id": "10_quiz",
        "name": "Quiz",
        "screenshot": "10_quiz.png",
        "narration": (
            "Built-in quizzes with instant scoring assess comprehension "
            "and identify knowledge gaps across your organization."
        ),
        "duration": 7,
        "renderer": render_scene_quiz,
    },
    {
        "id": "11_back_catalogue",
        "name": "Back to Catalogue",
        "screenshot": "11_back_catalogue.png",
        "narration": (
            "From catalogue to course to module to assessment, "
            "the complete learning experience, generated by AI from your existing content."
        ),
        "duration": 7,
        "renderer": render_scene_back_catalogue,
    },
    {
        "id": "12_closing",
        "name": "Closing",
        "screenshot": "12_closing.png",
        "narration": (
            "PureWork Training Studio transforms your documents into a complete learning platform. "
            "Visit purebrain dot A I to learn more."
        ),
        "duration": 8,
        "renderer": render_scene_closing,
    },
]


# ---------------------------------------------------------------------------
# Phase 1: Render Scene Frames
# ---------------------------------------------------------------------------
def render_frames():
    """Render all scene frames as 1920x1080 PNGs with Pillow."""
    print("\n=== PHASE 1: Rendering Scene Frames ===\n")
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    for scene in SCENES:
        output_path = SCREENSHOTS_DIR / scene["screenshot"]
        print(f"  [{scene['id']}] {scene['name']}...")
        try:
            scene["renderer"](output_path)
            if output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                print(f"    -> Saved: {output_path} ({size_kb:.0f} KB)")
            else:
                print(f"    !! File not created: {output_path}")
        except Exception as e:
            print(f"    !! Error rendering {scene['id']}: {e}")
            import traceback
            traceback.print_exc()

    print("\n  All frames rendered.\n")


# ---------------------------------------------------------------------------
# Phase 2: TTS Audio Generation
# ---------------------------------------------------------------------------
async def generate_audio(voice: str = "en-US-GuyNeural"):
    """Generate narration audio for each scene using edge-tts."""
    import edge_tts

    print("\n=== PHASE 2: Generating TTS Audio ===\n")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    for scene in SCENES:
        audio_path = AUDIO_DIR / f"{scene['id']}.mp3"
        print(f"  [{scene['id']}] Generating audio...")

        try:
            communicate = edge_tts.Communicate(scene["narration"], voice)
            await communicate.save(str(audio_path))
            if audio_path.exists():
                size_kb = audio_path.stat().st_size / 1024
                print(f"    -> Saved: {audio_path} ({size_kb:.0f} KB)")
            else:
                print(f"    !! File not created")
        except Exception as e:
            print(f"    !! Error generating audio for {scene['id']}: {e}")
            # Create a silent audio file as fallback
            duration = scene["duration"]
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"anullsrc=r=44100:cl=mono",
                "-t", str(duration),
                "-c:a", "aac", "-b:a", "128k",
                str(audio_path)
            ], capture_output=True)
            print(f"    -> Created silent fallback: {audio_path}")

    print("\n  All audio files generated.\n")


# ---------------------------------------------------------------------------
# Phase 3: ffmpeg Video Compilation
# ---------------------------------------------------------------------------
def get_audio_duration(audio_path: str) -> float:
    """Get the duration of an audio file using ffmpeg (no ffprobe needed)."""
    try:
        # Use ffmpeg to read the file and extract duration from stderr
        result = subprocess.run(
            ["ffmpeg", "-i", audio_path, "-f", "null", "-"],
            capture_output=True, text=True
        )
        # Parse duration from ffmpeg output: "Duration: 00:00:06.07"
        import re
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", result.stderr)
        if match:
            h, m, s, cs = match.groups()
            return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100
    except Exception:
        pass
    return 6.0


def compile_video():
    """Compile scene frames + audio into individual scene videos, then concatenate."""
    print("\n=== PHASE 3: Compiling Video with ffmpeg ===\n")
    SCENES_DIR.mkdir(parents=True, exist_ok=True)

    segment_files = []

    for i, scene in enumerate(SCENES):
        screenshot_path = SCREENSHOTS_DIR / scene["screenshot"]
        audio_path = AUDIO_DIR / f"{scene['id']}.mp3"
        segment_path = SCENES_DIR / f"{scene['id']}.mp4"

        if not screenshot_path.exists():
            print(f"  !! Missing frame: {screenshot_path}, skipping")
            continue

        # Get actual audio duration
        audio_dur = get_audio_duration(str(audio_path)) if audio_path.exists() else 0
        # Total = audio + 1.5s padding, minimum = scene duration
        total_duration = max(audio_dur + 1.5, scene["duration"])

        print(f"  [{scene['id']}] {scene['name']} "
              f"(audio={audio_dur:.1f}s, total={total_duration:.1f}s)...")

        if audio_path.exists():
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(screenshot_path),
                "-i", str(audio_path),
                "-vf",
                (
                    f"format=yuv420p,"
                    f"fade=t=in:st=0:d=0.5,"
                    f"fade=t=out:st={total_duration - 0.5}:d=0.5"
                ),
                "-af",
                (
                    f"afade=t=in:st=0:d=0.3,"
                    f"afade=t=out:st={total_duration - 0.5}:d=0.5,"
                    f"apad=pad_dur=2"
                ),
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-tune", "stillimage",
                "-threads", "1",
                "-c:a", "aac", "-b:a", "192k",
                "-r", "30",
                "-t", f"{total_duration:.2f}",
                str(segment_path)
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(screenshot_path),
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-vf",
                (
                    f"format=yuv420p,"
                    f"fade=t=in:st=0:d=0.5,"
                    f"fade=t=out:st={total_duration - 0.5}:d=0.5"
                ),
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-threads", "1",
                "-c:a", "aac", "-b:a", "192k",
                "-r", "30",
                "-t", f"{total_duration:.2f}",
                "-shortest",
                str(segment_path)
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    !! ffmpeg error: {result.stderr[-500:]}")
            continue

        segment_files.append(segment_path)
        print(f"    -> Saved: {segment_path}")

    if not segment_files:
        print("\n  !! No segments created. Cannot concatenate.")
        return

    # Create concat file list
    concat_file = SCENES_DIR / "filelist.txt"
    with open(concat_file, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    print(f"\n  Concatenating {len(segment_files)} segments...")

    # Concatenate with re-encode for consistent output
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-threads", "1",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(OUTPUT_FILE)
    ]

    result = subprocess.run(cmd_concat, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  !! Concatenation error (re-encode): {result.stderr[-300:]}")
        # Fallback: concat with stream copy
        print("  Retrying with stream copy...")
        cmd_copy = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-movflags", "+faststart",
            str(OUTPUT_FILE)
        ]
        result2 = subprocess.run(cmd_copy, capture_output=True, text=True)
        if result2.returncode != 0:
            print(f"  !! Copy concat also failed: {result2.stderr[-300:]}")
            return

    # Output info
    if OUTPUT_FILE.exists():
        size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
        total_dur = get_audio_duration(str(OUTPUT_FILE))
        print(f"\n  {'=' * 40}")
        print(f"  OUTPUT VIDEO")
        print(f"  {'=' * 40}")
        print(f"  File:       {OUTPUT_FILE}")
        print(f"  Size:       {size_mb:.1f} MB")
        print(f"  Duration:   {total_dur:.1f}s ({total_dur/60:.1f} min)")
        print(f"  Resolution: 1920x1080")
        print(f"  Codec:      H.264 + AAC")
        print(f"  {'=' * 40}\n")
    else:
        print(f"\n  !! Output file not created at {OUTPUT_FILE}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="PureWork Training Studio Video Walkthrough Generator")
    parser.add_argument("--voice", default="en-US-GuyNeural",
                        help="TTS voice (default: en-US-GuyNeural)")
    parser.add_argument("--skip-frames", action="store_true",
                        help="Skip frame rendering (use existing PNGs)")
    parser.add_argument("--skip-audio", action="store_true",
                        help="Skip audio generation (use existing)")
    parser.add_argument("--skip-video", action="store_true",
                        help="Skip video compilation")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available TTS voices and exit")
    args = parser.parse_args()

    if args.list_voices:
        import edge_tts
        voices = await edge_tts.list_voices()
        en_voices = [v for v in voices if v["Locale"].startswith("en-")]
        print("\nAvailable English TTS voices:\n")
        for v in sorted(en_voices, key=lambda x: x["ShortName"]):
            print(f"  {v['ShortName']:35s} {v['Gender']:8s} {v['Locale']}")
        return

    print("=" * 60)
    print("  PureWork Training Studio")
    print("  Video Walkthrough Generator")
    print("=" * 60)
    print(f"\n  Voice:  {args.voice}")
    print(f"  Output: {OUTPUT_FILE}\n")

    start_time = time.time()

    # Phase 1: Render frames
    if not args.skip_frames:
        render_frames()
    else:
        print("\n  [Skipping frame rendering -- using existing PNGs]\n")

    # Phase 2: TTS Audio
    if not args.skip_audio:
        await generate_audio(voice=args.voice)
    else:
        print("\n  [Skipping audio -- using existing files]\n")

    # Phase 3: Video Compilation
    if not args.skip_video:
        compile_video()
    else:
        print("\n  [Skipping video compilation]\n")

    elapsed = time.time() - start_time
    print(f"\n  Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Done!\n")


if __name__ == "__main__":
    asyncio.run(main())

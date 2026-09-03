#!/usr/bin/env python3
"""
PureWork Training Studio — Video Walkthrough Pipeline

Generates a professional narrated video walkthrough by:
  1. Driving the app with headless Playwright, capturing 1920x1080 stills
  2. Generating narration audio with edge-tts (Microsoft TTS)
  3. Compiling stills + audio into a polished MP4 with ffmpeg

Output: PureWork_Training_Studio_Walkthrough.mp4

Usage:
  python3 generate_walkthrough.py [--voice en-US-GuyNeural] [--skip-screenshots] [--skip-audio]
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.resolve()
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
AUDIO_DIR = BASE_DIR / "audio"
SCENES_DIR = BASE_DIR / "scenes"
OUTPUT_FILE = BASE_DIR / "PureWork_Training_Studio_Walkthrough.mp4"

# The local HTML file
APP_HTML = Path("/home/aiciv/purework-ai/docs/index.html").resolve()
APP_URL = f"file://{APP_HTML}"

# Login credentials
LOGIN_EMAIL = "admin@demo.com"
LOGIN_PASSWORD = "password123"

# ---------------------------------------------------------------------------
# Scene Definitions
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
        "actions": "navigate_to_app",
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
        "actions": "login_and_dashboard",
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
        "actions": "go_to_catalogue",
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
        "actions": "search_safety",
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
        "actions": "open_course",
    },
    {
        "id": "06_ai_insights",
        "name": "Module Content — AI Insights",
        "screenshot": "06_ai_insights.png",
        "narration": (
            "Every module includes an AI-generated insights panel with key terms, "
            "risk areas, and a comprehensive summary."
        ),
        "duration": 8,
        "actions": "open_module_insights",
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
        "actions": "show_podcast",
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
        "actions": "show_chat",
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
        "actions": "show_studyguide",
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
        "actions": "show_quiz",
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
        "actions": "back_to_catalogue",
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
        "actions": "closing_card",
    },
]


# ---------------------------------------------------------------------------
# Phase 1: Screenshot Capture with Playwright
# ---------------------------------------------------------------------------
async def capture_screenshots():
    """Drive the app with Playwright and capture each scene as a 1920x1080 PNG."""
    from playwright.async_api import async_playwright

    print("\n=== PHASE 1: Capturing Screenshots ===\n")
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()

        for scene in SCENES:
            action = scene["actions"]
            screenshot_path = SCREENSHOTS_DIR / scene["screenshot"]
            print(f"  [{scene['id']}] {scene['name']}...")

            try:
                if action == "navigate_to_app":
                    await page.goto(APP_URL, wait_until="networkidle")
                    await page.wait_for_timeout(2000)

                elif action == "login_and_dashboard":
                    await page.fill("#login-email", LOGIN_EMAIL)
                    await page.fill("#login-password", LOGIN_PASSWORD)
                    await page.click("#login-btn")
                    await page.wait_for_timeout(2500)

                elif action == "go_to_catalogue":
                    await page.evaluate("navigate('studio')")
                    await page.wait_for_timeout(2500)

                elif action == "search_safety":
                    # Type "safety" into the search input
                    search_input = page.locator("#tour-target-search input, .studio-search input, input[placeholder*='Search']")
                    if await search_input.count() > 0:
                        await search_input.first.fill("safety")
                        await page.wait_for_timeout(1500)
                    else:
                        # Fallback: execute search via JS
                        await page.evaluate("""
                            var el = document.querySelector('input[type="text"][placeholder*="earch"]');
                            if (el) { el.value = 'safety'; el.dispatchEvent(new Event('input')); }
                        """)
                        await page.wait_for_timeout(1500)

                elif action == "open_course":
                    # Clear search first, then click first active course
                    await page.evaluate("""
                        var el = document.querySelector('input[type="text"][placeholder*="earch"]');
                        if (el) { el.value = ''; el.dispatchEvent(new Event('input')); }
                    """)
                    await page.wait_for_timeout(800)
                    await page.evaluate("""
                        var firstCourse = STUDIO_COURSES.find(function(c) { return isCourseActive(c); });
                        if (firstCourse) catalogueShowCourse(firstCourse.id);
                    """)
                    await page.wait_for_timeout(2000)

                elif action == "open_module_insights":
                    # Click the first module in the course
                    await page.evaluate("""
                        var course = STUDIO_COURSES.find(function(c) { return c.id === _studioState.selectedCourse; });
                        if (course && course.modules.length > 0) {
                            catalogueShowModule ? catalogueShowModule(course.id, course.modules[0]) : selectSOP(course.modules[0]);
                        }
                    """)
                    await page.wait_for_timeout(2000)
                    # Ensure insights panel is visible
                    await page.evaluate("""
                        _studioState.insightsRevealed = true;
                        var sopId = _studioState.selectedSop;
                        var richData = STUDIO_RICH_DATA[sopId];
                        if (richData && richData.insights) {
                            var container = document.getElementById('studio-insights-container');
                            var sop = STUDIO_SOPS.find(function(s) { return s.id === sopId; });
                            if (container && sop) {
                                container.innerHTML = renderInsightsPanel(sop, richData.insights);
                            }
                        }
                    """)
                    await page.wait_for_timeout(1500)

                elif action == "show_podcast":
                    await page.evaluate("setStudioOutput('podcast')")
                    await page.wait_for_timeout(2000)

                elif action == "show_chat":
                    await page.evaluate("setStudioOutput('chat')")
                    await page.wait_for_timeout(2000)

                elif action == "show_studyguide":
                    await page.evaluate("setStudioOutput('studyguide')")
                    await page.wait_for_timeout(2000)

                elif action == "show_quiz":
                    await page.evaluate("setStudioOutput('quiz')")
                    await page.wait_for_timeout(2000)

                elif action == "back_to_catalogue":
                    await page.evaluate("catalogueShowGrid()")
                    await page.wait_for_timeout(2000)

                elif action == "closing_card":
                    # Generate a closing title card using Pillow, no screenshot needed
                    _generate_closing_card(screenshot_path)
                    print(f"    -> Created closing card: {screenshot_path}")
                    continue

                # Take the screenshot
                await page.screenshot(path=str(screenshot_path), full_page=False)
                print(f"    -> Saved: {screenshot_path}")

            except Exception as e:
                print(f"    !! Error on scene {scene['id']}: {e}")
                # Try to capture whatever is on screen
                try:
                    await page.screenshot(path=str(screenshot_path), full_page=False)
                    print(f"    -> Saved fallback screenshot: {screenshot_path}")
                except Exception:
                    print(f"    !! Could not capture fallback screenshot")

        await browser.close()

    print("\n  All screenshots captured.\n")


def _generate_closing_card(output_path: Path):
    """Create a branded closing card with Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), color=(15, 17, 26))
    draw = ImageDraw.Draw(img)

    # Try to load a nice font; fall back to default
    def get_font(size, bold=False):
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                return ImageFont.truetype(fp, size)
        return ImageFont.load_default()

    # Draw a subtle gradient overlay (horizontal band)
    for y in range(height):
        # Dark blue to dark purple gradient
        r = int(15 + (y / height) * 15)
        g = int(17 + (y / height) * 5)
        b = int(26 + (y / height) * 40)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Accent line at top
    draw.rectangle([(0, 0), (width, 4)], fill=(99, 102, 241))

    # Main title
    title_font = get_font(72, bold=True)
    title_text = "PureWork Training Studio"
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) / 2, 340), title_text, fill=(255, 255, 255), font=title_font)

    # Subtitle
    subtitle_font = get_font(36)
    subtitle_text = "Enterprise Training, Powered by AI"
    bbox2 = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    sw = bbox2[2] - bbox2[0]
    draw.text(((width - sw) / 2, 440), subtitle_text, fill=(165, 170, 210), font=subtitle_font)

    # Accent divider
    div_y = 510
    div_w = 200
    draw.rectangle([((width - div_w) / 2, div_y), ((width + div_w) / 2, div_y + 3)],
                    fill=(99, 102, 241))

    # URL
    url_font = get_font(32)
    url_text = "purebrain.ai"
    bbox3 = draw.textbbox((0, 0), url_text, font=url_font)
    uw = bbox3[2] - bbox3[0]
    draw.text(((width - uw) / 2, 560), url_text, fill=(99, 102, 241), font=url_font)

    # Footer
    footer_font = get_font(20)
    footer_text = "Pure Technology  |  Reimagining Data Innovation"
    bbox4 = draw.textbbox((0, 0), footer_text, font=footer_font)
    fw = bbox4[2] - bbox4[0]
    draw.text(((width - fw) / 2, 940), footer_text, fill=(100, 105, 140), font=footer_font)

    img.save(str(output_path), "PNG")


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
            print(f"    -> Saved: {audio_path}")
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
    """Get the duration of an audio file using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except (ValueError, Exception):
        return 6.0  # Default fallback


def compile_video():
    """Compile screenshots + audio into individual scene videos, then concatenate."""
    print("\n=== PHASE 3: Compiling Video with ffmpeg ===\n")
    SCENES_DIR.mkdir(parents=True, exist_ok=True)

    segment_files = []

    for i, scene in enumerate(SCENES):
        screenshot_path = SCREENSHOTS_DIR / scene["screenshot"]
        audio_path = AUDIO_DIR / f"{scene['id']}.mp3"
        segment_path = SCENES_DIR / f"{scene['id']}.mp4"

        if not screenshot_path.exists():
            print(f"  !! Missing screenshot: {screenshot_path}, skipping")
            continue

        # Get actual audio duration, use whichever is longer (audio or scene duration)
        audio_dur = get_audio_duration(str(audio_path)) if audio_path.exists() else 0
        # Add 1.5 seconds of padding after narration ends
        total_duration = max(audio_dur + 1.5, scene["duration"])
        total_frames = int(total_duration * 30)

        print(f"  [{scene['id']}] {scene['name']} "
              f"(audio={audio_dur:.1f}s, total={total_duration:.1f}s)...")

        # Calculate zoom speed for Ken Burns effect (100% -> 105% over duration)
        # zoompan z formula: starts at 1.0, ends at 1.05
        zoom_increment = 0.05 / total_frames if total_frames > 0 else 0.0001

        # Build the ffmpeg command
        if audio_path.exists():
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(screenshot_path),
                "-i", str(audio_path),
                "-filter_complex",
                (
                    f"[0:v]zoompan=z='min(zoom+{zoom_increment:.8f},1.05)'"
                    f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                    f":d={total_frames}:s=1920x1080:fps=30,"
                    f"fade=t=in:st=0:d=0.5,fade=t=out:st={total_duration - 0.5}:d=0.5"
                    f"[v];"
                    f"[1:a]afade=t=in:st=0:d=0.3,afade=t=out:st={total_duration - 0.5}:d=0.5"
                    f",apad=pad_dur=2[a]"
                ),
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", f"{total_duration:.2f}",
                str(segment_path)
            ]
        else:
            # No audio - create video-only segment with silent audio
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(screenshot_path),
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
                "-filter_complex",
                (
                    f"[0:v]zoompan=z='min(zoom+{zoom_increment:.8f},1.05)'"
                    f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                    f":d={total_frames}:s=1920x1080:fps=30,"
                    f"fade=t=in:st=0:d=0.5,fade=t=out:st={total_duration - 0.5}:d=0.5"
                    f"[v]"
                ),
                "-map", "[v]", "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
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

    # Create the concat file list
    concat_file = SCENES_DIR / "filelist.txt"
    with open(concat_file, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    print(f"\n  Concatenating {len(segment_files)} segments...")

    # Concatenate all segments
    # Use re-encode method for consistent output (concat demuxer can have issues
    # if individual segments have slightly different stream properties)
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(OUTPUT_FILE)
    ]

    result = subprocess.run(cmd_concat, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  !! Concatenation error: {result.stderr[-500:]}")
        # Try simpler concat with copy
        print("  Retrying with stream copy...")
        cmd_concat_copy = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-movflags", "+faststart",
            str(OUTPUT_FILE)
        ]
        result2 = subprocess.run(cmd_concat_copy, capture_output=True, text=True)
        if result2.returncode != 0:
            print(f"  !! Copy concat also failed: {result2.stderr[-300:]}")
            return

    # Get output file info
    if OUTPUT_FILE.exists():
        size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
        duration_result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(OUTPUT_FILE)],
            capture_output=True, text=True
        )
        total_dur = float(duration_result.stdout.strip()) if duration_result.stdout.strip() else 0
        print(f"\n  === OUTPUT ===")
        print(f"  File: {OUTPUT_FILE}")
        print(f"  Size: {size_mb:.1f} MB")
        print(f"  Duration: {total_dur:.1f} seconds ({total_dur/60:.1f} minutes)")
        print(f"  Resolution: 1920x1080")
        print(f"  ===============\n")
    else:
        print(f"\n  !! Output file not created at {OUTPUT_FILE}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    import argparse

    parser = argparse.ArgumentParser(description="PureWork Training Studio Video Walkthrough Generator")
    parser.add_argument("--voice", default="en-US-GuyNeural",
                        help="TTS voice (default: en-US-GuyNeural)")
    parser.add_argument("--skip-screenshots", action="store_true",
                        help="Skip screenshot capture (use existing)")
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
    print("  PureWork Training Studio — Video Walkthrough Generator")
    print("=" * 60)
    print(f"\n  App:    {APP_URL}")
    print(f"  Voice:  {args.voice}")
    print(f"  Output: {OUTPUT_FILE}\n")

    start_time = time.time()

    # Phase 1: Screenshots
    if not args.skip_screenshots:
        await capture_screenshots()
    else:
        print("\n  [Skipping screenshots — using existing files]\n")

    # Phase 2: TTS Audio
    if not args.skip_audio:
        await generate_audio(voice=args.voice)
    else:
        print("\n  [Skipping audio — using existing files]\n")

    # Phase 3: Video Compilation
    if not args.skip_video:
        compile_video()
    else:
        print("\n  [Skipping video compilation]\n")

    elapsed = time.time() - start_time
    print(f"\n  Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"  Done!\n")


if __name__ == "__main__":
    asyncio.run(main())

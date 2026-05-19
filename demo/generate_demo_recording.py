from __future__ import annotations

import textwrap
import wave
from pathlib import Path

import numpy as np
import pyttsx3
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "demo" / "screenshots"
OUT_DIR = ROOT / "demo" / "recording"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720


SEGMENTS = [
    (
        "AI-First HCP CRM Module",
        "01-dashboard.png",
        "This demo presents an AI-first Customer Relationship Management module for healthcare professional engagement. "
        "The assignment requires React, Redux, FastAPI, LangGraph, Groq gemma two nine b instruction tuned, and a SQL database. "
        "The product is designed for field representatives in life sciences who need to capture high quality HCP interactions quickly, consistently, and with compliance awareness. "
        "The first screen is not a landing page. It is the working CRM surface where the representative can select an HCP, review context, log an interaction, and run AI tools without changing systems.",
    ),
    (
        "Field Representative Workspace",
        "01-dashboard.png",
        "The left rail lists healthcare professionals with specialty, territory, preferred channel, and tier. "
        "Selecting an HCP loads a focused workspace with organization, persona notes, commercial context, and recent engagement intelligence. "
        "This matters because a representative has limited time before or after a call. The screen is optimized for scanning, action, and auditability instead of decorative marketing content.",
    ),
    (
        "Interaction Intelligence",
        "01-dashboard.png",
        "The insights strip shows the number of interactions, average quality score, compliance flags, and top discussion topic. "
        "These metrics are derived from the interaction records and make the module feel like an operating dashboard rather than a plain form. "
        "Quality score rewards detailed notes, captured topics, products, follow-up commitments, and clear next actions. Compliance signals reduce the score when risk appears.",
    ),
    (
        "Structured Log Interaction",
        "01-dashboard.png",
        "The structured form supports channel, interaction type, sentiment, follow-up date, products, topics, objections, commitments, executive summary, and raw field notes. "
        "The raw notes remain available for audit while the AI enrichment adds normalized CRM fields. "
        "This gives the representative flexibility without losing data quality.",
    ),
    (
        "Conversational Logging",
        "03-ai-chat.png",
        "The AI chat path is for natural language capture. A representative can type a quick note after a meeting, and LangGraph routes the message to the correct tool. "
        "The log interaction tool then uses the LLM to summarize the note, extract topics and products, identify objections and commitments, infer sentiment, score quality, flag compliance risk, and suggest the next best action.",
    ),
    (
        "LangGraph Tool Registry",
        "02-compliance-tool.png",
        "The backend defines a LangGraph agent with a route node and an execute tool node. "
        "The tool registry includes log interaction, edit interaction, get HCP profile, suggest next best action, draft follow-up, and compliance review. "
        "The assignment asks for at least five tools, and this implementation includes a sixth compliance tool to make the workflow more realistic for life sciences.",
    ),
    (
        "Compliance Review",
        "02-compliance-tool.png",
        "The compliance review tool checks the latest interaction for off-label requests, adverse event language, sample requests, and patient-identifiable information. "
        "When a risk is present, the tool recommends escalation before follow-up. When the record is clear, the representative can proceed with approved materials. "
        "The point is not to replace compliance teams. It is to catch risk early and make the field workflow safer.",
    ),
    (
        "Next Best Action",
        "02-compliance-tool.png",
        "The next best action tool combines HCP profile, tier, preferred channel, specialty, and recent interaction history. "
        "It returns a concise recommendation that a field representative can act on immediately. "
        "For example, it may suggest sending an approved access sheet, scheduling a data-focused follow-up, or using the HCP's preferred communication channel.",
    ),
    (
        "Follow-Up Drafting",
        "02-compliance-tool.png",
        "The follow-up draft tool creates a short email grounded in the latest interaction. "
        "The prompt explicitly avoids unsupported promotional claims and keeps the message factual. "
        "This demonstrates how LLMs can reduce administrative burden while still respecting regulated communication constraints.",
    ),
    (
        "Technical Structure",
        "01-dashboard.png",
        "The frontend is built with React, Redux Toolkit, Vite, Google Inter, and lucide icons. "
        "The backend is FastAPI with SQLAlchemy models for HCPs and interactions. "
        "PostgreSQL is supported through Docker Compose, while SQLite demo mode is available for quick local testing. "
        "The API documentation is available through FastAPI docs, and tests validate the agent tool flow.",
    ),
    (
        "Submission Summary",
        "01-dashboard.png",
        "In summary, this project satisfies the assignment and adds industry-level depth: dual entry modes, LangGraph orchestration, Groq model wiring, six sales and compliance tools, AI enrichment, quality scoring, compliance flags, dashboard insights, Docker support, tests, documentation, and a clear recording script. "
        "For final submission, push the repository to GitHub, record the live walkthrough with your real Groq API key, and submit the GitHub link plus recording link in the Google Form.",
    ),
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/Inter.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def make_slide(title: str, image_name: str, narration: str, index: int) -> Path:
    base = Image.new("RGB", (W, H), "#eef2f1")
    draw = ImageDraw.Draw(base)
    title_font = load_font(42, bold=True)
    body_font = load_font(24)
    label_font = load_font(18, bold=True)

    screenshot_path = SCREENSHOTS / image_name
    if screenshot_path.exists():
        shot = Image.open(screenshot_path).convert("RGB")
        shot.thumbnail((760, 600))
        x = 36
        y = 76
        base.paste(shot, (x, y))
        draw.rounded_rectangle((x - 8, y - 8, x + shot.width + 8, y + shot.height + 8), radius=12, outline="#cad7d2", width=2)

    draw.text((840, 76), title, fill="#172323", font=title_font)
    draw.text((840, 46), "AI-FIRST HCP CRM DEMO", fill="#236d5a", font=label_font)
    lines = wrap(draw, narration, body_font, 370)
    y = 150
    for line in lines[:13]:
        draw.text((840, y), line, fill="#2f3d39", font=body_font)
        y += 34
    draw.rounded_rectangle((840, 610, 1216, 664), radius=8, fill="#172323")
    draw.text((864, 626), f"Section {index + 1:02d} of {len(SEGMENTS):02d}", fill="#f5fbf8", font=label_font)

    out = OUT_DIR / f"slide_{index:02d}.png"
    base.save(out)
    return out


def narration_text() -> str:
    chunks = []
    for title, _, text in SEGMENTS:
        chunks.append(f"{title}. {text}")
    return "\n\n".join(chunks)


def create_audio() -> Path:
    audio_path = OUT_DIR / "demo_narration.wav"
    engine = pyttsx3.init()
    engine.setProperty("rate", 80)
    engine.save_to_file(narration_text(), str(audio_path))
    engine.runAndWait()
    return audio_path


def audio_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / float(wav.getframerate())


def main() -> None:
    slide_paths = [make_slide(title, image, textwrap.fill(text, 100), index) for index, (title, image, text) in enumerate(SEGMENTS)]
    audio_path = create_audio()
    duration = max(audio_duration(audio_path), 60.0)
    total_words = sum(len(text.split()) for _, _, text in SEGMENTS)

    clips = []
    for slide_path, (_, _, text) in zip(slide_paths, SEGMENTS, strict=True):
        weight = len(text.split()) / total_words
        clips.append(ImageClip(np.array(Image.open(slide_path))).with_duration(duration * weight))

    video = concatenate_videoclips(clips, method="compose").with_audio(AudioFileClip(str(audio_path)))
    out_mp4 = OUT_DIR / "hcp_ai_crm_demo_recording.mp4"
    video.write_videofile(
        str(out_mp4),
        fps=12,
        codec="libx264",
        audio_codec="aac",
        bitrate="1400k",
        preset="veryfast",
        logger=None,
    )
    print(out_mp4)


if __name__ == "__main__":
    main()

import json
import pathlib
import textwrap
import os
from PIL import Image, ImageDraw, ImageFont

CANVAS_W, CANVAS_H = 1080, 1350

SLIDE_CONTENT = [
    {"type": "hook", "text": None},  # filled from hooks.json
    {"type": "tip", "text": "Most people react.\nThe Stoic responds."},
    {"type": "tip", "text": "You control your thoughts.\nNot outcomes."},
    {"type": "tip", "text": "Discomfort is\nthe price of growth."},
    {"type": "tip", "text": "Memento mori.\nDeath makes today matter."},
    {"type": "tip", "text": "Amor fati.\nLove what happens to you."},
    {"type": "tip", "text": "The obstacle\nis the way. Always."},
    {"type": "tip", "text": "Ego is the enemy\nof progress."},
    {"type": "tip", "text": "Strong mind.\nCalm spirit. Clear action."},
    {"type": "cta", "text": "Save this.\nCome back when life gets hard."},
]

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fit_and_crop(img):
    target_ratio = CANVAS_W / CANVAS_H
    img_ratio = img.width / img.height
    if img_ratio > target_ratio:
        new_h = CANVAS_H
        new_w = int(new_h * img_ratio)
    else:
        new_w = CANVAS_W
        new_h = int(new_w / img_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - CANVAS_W) // 2
    top = (new_h - CANVAS_H) // 2
    return img.crop((left, top, left + CANVAS_W, top + CANVAS_H))

def add_overlay(img, alpha=170):
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def draw_centered_text(draw, lines, font, y_start, line_height, color="white"):
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((CANVAS_W - w) // 2, y_start), line, font=font, fill=color)
        y_start += line_height

def compose_slide(img_path, content, slide_num):
    img = Image.open(img_path).convert("RGB")
    img = fit_and_crop(img)
    img = add_overlay(img, alpha=160)
    draw = ImageDraw.Draw(img)

    text = content["text"]
    slide_type = content["type"]

    if slide_type == "hook":
        font = get_font(68, bold=True)
        lines = textwrap.wrap(text, width=16)
        total_h = len(lines) * 85
        draw_centered_text(draw, lines, font, (CANVAS_H - total_h) // 2, 85)
        small = get_font(30)
        draw.text((40, CANVAS_H - 55), f"{slide_num} / 10", font=small, fill=(180, 180, 180))

    elif slide_type == "cta":
        font = get_font(60, bold=True)
        lines = text.split("\n")
        total_h = len(lines) * 75
        draw_centered_text(draw, lines, font, (CANVAS_H - total_h) // 2, 75)
        small = get_font(30)
        draw.text((40, CANVAS_H - 55), f"{slide_num} / 10", font=small, fill=(180, 180, 180))

    else:
        font = get_font(56, bold=True)
        lines = text.split("\n")
        total_h = len(lines) * 70
        draw_centered_text(draw, lines, font, (CANVAS_H - total_h) // 2, 70)
        small = get_font(30)
        draw.text((40, CANVAS_H - 55), f"{slide_num} / 10", font=small, fill=(180, 180, 180))

    return img

def run():
    hooks_data = json.loads(pathlib.Path("data/current_run/hooks.json").read_text())
    image_data = json.loads(pathlib.Path("data/current_run/image_paths.json").read_text())

    SLIDE_CONTENT[0]["text"] = hooks_data["selected"]["text"]

    out_dir = pathlib.Path("data/current_run/slides")
    out_dir.mkdir(parents=True, exist_ok=True)

    images = image_data["images"]
    slide_paths = []

    for i, (content, img_path) in enumerate(zip(SLIDE_CONTENT, images)):
        slide = compose_slide(img_path, content, i + 1)
        out_path = out_dir / f"slide_{i+1:02d}.jpg"
        slide.save(str(out_path), "JPEG", quality=95)
        slide_paths.append(str(out_path))
        print(f"  Composed slide {i+1}/10")

    pathlib.Path("data/current_run/slide_paths.json").write_text(
        json.dumps({"slides": slide_paths}, indent=2)
    )
    print(f"Done. {len(slide_paths)} slides at {CANVAS_W}x{CANVAS_H}")

if __name__ == "__main__":
    run()

import json
import pathlib
import textwrap
import os
from PIL import Image, ImageDraw, ImageFont

CANVAS_W, CANVAS_H = 1080, 1350

CTA_TEXT = "Save this.\nCome back when life gets hard."

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

    PADDING = 80  # px from each side

    def wrap_and_fit(raw_text, base_size, wrap_width, line_height_ratio=1.3):
        """Wrap text and shrink font until all lines fit within canvas width."""
        size = base_size
        while size > 24:
            font = get_font(size, bold=True)
            # Flatten \n then re-wrap at wrap_width chars
            flat = raw_text.replace("\n", " ")
            lines = textwrap.wrap(flat, width=wrap_width)
            # Check no line exceeds canvas width minus padding
            max_w = max(draw.textbbox((0,0), l, font=font)[2] for l in lines)
            if max_w <= CANVAS_W - PADDING * 2:
                line_h = int(size * line_height_ratio)
                return font, lines, line_h
            size -= 4
        font = get_font(size, bold=True)
        flat = raw_text.replace("\n", " ")
        lines = textwrap.wrap(flat, width=wrap_width)
        return font, lines, int(size * line_height_ratio)

    small = get_font(30)

    if slide_type == "hook":
        font, lines, line_h = wrap_and_fit(text, 68, 18)
        total_h = len(lines) * line_h
        draw_centered_text(draw, lines, font, (CANVAS_H - total_h) // 2, line_h)

    elif slide_type == "cta":
        font, lines, line_h = wrap_and_fit(text, 60, 20)
        total_h = len(lines) * line_h
        draw_centered_text(draw, lines, font, (CANVAS_H - total_h) // 2, line_h)

    else:
        font, lines, line_h = wrap_and_fit(text, 56, 22)
        total_h = len(lines) * line_h
        draw_centered_text(draw, lines, font, (CANVAS_H - total_h) // 2, line_h)

    draw.text((40, CANVAS_H - 55), f"{slide_num} / 10", font=small, fill=(180, 180, 180))

    return img

def run():
    hooks_data = json.loads(pathlib.Path("data/current_run/hooks.json").read_text())
    image_data = json.loads(pathlib.Path("data/current_run/image_paths.json").read_text())

    # Build slide content dynamically from Claude-generated texts
    slide_content = [{"type": "hook", "text": hooks_data["selected"]["text"]}]
    for tip in hooks_data["slides"][:8]:
        slide_content.append({"type": "tip", "text": tip})
    slide_content.append({"type": "cta", "text": CTA_TEXT})

    out_dir = pathlib.Path("data/current_run/slides")
    out_dir.mkdir(parents=True, exist_ok=True)

    images = image_data["images"]
    slide_paths = []

    for i, (content, img_path) in enumerate(zip(slide_content, images)):
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

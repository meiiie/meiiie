from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "meiiie-signature-imagegen-source.png"
OUTPUT = ASSETS / "meiiie-signature.gif"
PREVIEW = ASSETS / "meiiie-signature.png"

WIDTH = 960
HEIGHT = 300
FRAMES = 84
FRAME_MS = 72


def ease_in_out(value: float) -> float:
    return 0.5 - 0.5 * math.cos(max(0.0, min(1.0, value)) * math.pi)


def cover_crop(image: Image.Image, width: int, height: int, y_bias: float = 0.46) -> Image.Image:
    src_w, src_h = image.size
    target_ratio = width / height
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        crop_h = src_h
        crop_w = int(crop_h * target_ratio)
        left = (src_w - crop_w) // 2
        top = 0
    else:
        crop_w = src_w
        crop_h = int(crop_w / target_ratio)
        left = 0
        top = int((src_h - crop_h) * y_bias)

    return image.crop((left, top, left + crop_w, top + crop_h)).resize(
        (width, height),
        Image.Resampling.LANCZOS,
    )


def shifted_frame(source: Image.Image, progress: float) -> Image.Image:
    zoom = 1.024 + 0.006 * math.sin(progress * math.tau)
    scaled = source.resize(
        (int(WIDTH * zoom), int(HEIGHT * zoom)),
        Image.Resampling.LANCZOS,
    )
    max_x = scaled.width - WIDTH
    max_y = scaled.height - HEIGHT
    pan_x = int((0.5 + 0.5 * math.sin(progress * math.tau)) * max_x)
    pan_y = int((0.5 + 0.5 * math.sin(progress * math.tau + math.pi / 2)) * max_y)
    return scaled.crop((pan_x, pan_y, pan_x + WIDTH, pan_y + HEIGHT))


def soft_light_sweep(progress: float) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    sweep_x = int(-WIDTH * 0.35 + (WIDTH * 1.7) * progress)

    for offset in range(-120, 121, 6):
        alpha = int(18 * (1 - abs(offset) / 126))
        if alpha <= 0:
            continue
        x = sweep_x + offset
        draw.line((x - 120, 0, x + 90, HEIGHT), fill=(114, 239, 255, alpha), width=4)

    return layer.filter(ImageFilter.GaussianBlur(7))


def pulse_highlights(frame: Image.Image, progress: float) -> Image.Image:
    glow = ImageEnhance.Contrast(frame.convert("L")).enhance(1.9)
    glow = glow.point(lambda value: max(0, min(255, int((value - 138) * 2.2))))
    glow = glow.filter(ImageFilter.GaussianBlur(3))

    alpha_strength = 0.12 + 0.08 * math.sin(progress * math.tau)
    alpha = glow.point(lambda value: int(value * alpha_strength))
    color = Image.new("RGBA", (WIDTH, HEIGHT), (92, 227, 255, 0))
    color.putalpha(alpha)
    return Image.alpha_composite(frame, color)


def render() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing imagegen source: {SOURCE}")

    ASSETS.mkdir(exist_ok=True)
    source = Image.open(SOURCE).convert("RGBA")
    base = cover_crop(source, WIDTH, HEIGHT)
    frames: list[Image.Image] = []

    for index in range(FRAMES):
        progress = index / FRAMES
        wave = ease_in_out((math.sin(progress * math.tau) + 1) / 2)

        frame = shifted_frame(base, progress)
        frame = pulse_highlights(frame, progress)
        frame = ImageChops.screen(frame, soft_light_sweep(wave))

        frames.append(frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=160))

    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    frames[24].convert("RGBA").save(PREVIEW)
    print(OUTPUT)
    print(PREVIEW)


if __name__ == "__main__":
    render()

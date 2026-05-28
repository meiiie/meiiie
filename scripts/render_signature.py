from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
WIDTH = 960
HEIGHT = 300
FRAMES = 96
FRAME_MS = 70

FONT_TITLE = Path("C:/Windows/Fonts/CascadiaCode.ttf")
FONT_TEXT = Path("C:/Windows/Fonts/segoeui.ttf")


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    x = clamp((value - edge0) / (edge1 - edge0))
    return x * x * (3 - 2 * x)


def ease_out_cubic(value: float) -> float:
    x = clamp(value)
    return 1 - pow(1 - x, 3)


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    if path.exists():
        return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


def text_size(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.FreeTypeFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font_obj)
    return right - left, bottom - top


def draw_centered(
    layer: Image.Image,
    text: str,
    y: int,
    font_obj: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    x_offset: int = 0,
) -> None:
    draw = ImageDraw.Draw(layer)
    tw, th = text_size(draw, text, font_obj)
    draw.text(((WIDTH - tw) // 2 + x_offset, y - th // 2), text, font=font_obj, fill=fill)


def draw_background(base: Image.Image, progress: float) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    base.paste((9, 14, 23), (0, 0, WIDTH, HEIGHT))

    for y in range(26, HEIGHT, 26):
        alpha = 12 + int(7 * math.sin(progress * math.tau + y * 0.04))
        draw.line((0, y, WIDTH, y), fill=(87, 108, 139, alpha), width=1)

    for x in range(40, WIDTH, 80):
        alpha = 10 + int(5 * math.sin(progress * math.tau + x * 0.02))
        draw.line((x, 0, x, HEIGHT), fill=(87, 108, 139, alpha), width=1)

    for offset, alpha, color in (
        (0.0, 58, (67, 185, 255)),
        (0.23, 42, (144, 116, 255)),
        (0.48, 34, (89, 255, 198)),
    ):
        points: list[tuple[float, float]] = []
        for x in range(-20, WIDTH + 21, 10):
            phase = x * 0.012 + progress * math.tau + offset * math.tau
            y = 258 + math.sin(phase) * 10 + math.sin(phase * 0.43) * 5
            points.append((x, y))
        draw.line(points, fill=(*color, alpha), width=2)


def draw_particles(base: Image.Image, progress: float, fade: float) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    random.seed(1789)

    for _ in range(46):
        seed_x = random.random()
        seed_y = random.random()
        drift = random.uniform(-22, 22)
        radius = random.choice((1, 1, 1, 2))
        phase = random.random()
        x = (seed_x * WIDTH + math.sin((progress + phase) * math.tau) * drift) % WIDTH
        y = 34 + seed_y * 206 + math.cos((progress + phase * 0.7) * math.tau) * drift * 0.45
        alpha = int((28 + 32 * math.sin((progress + phase) * math.tau) ** 2) * fade)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(151, 196, 255, alpha))


def draw_signature(base: Image.Image, progress: float) -> None:
    title_font = font(FONT_TITLE, 78)
    text_font = font(FONT_TEXT, 18)
    small_font = font(FONT_TEXT, 15)

    reveal = ease_out_cubic(smoothstep(0.08, 0.42, progress))
    hold = 1 - smoothstep(0.86, 0.98, progress)
    opacity = clamp(smoothstep(0.02, 0.12, progress) * hold)

    title = "meiiie"
    subtitle = "open-source / video systems / education / AI tooling"
    closing = "building useful software, carefully"

    title_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(title_layer)
    tw, th = text_size(draw, title, title_font)
    tx = (WIDTH - tw) // 2
    ty = 100 - th // 2

    mask_width = max(1, int((tw + 16) * reveal))
    title_mask = Image.new("L", (WIDTH, HEIGHT), 0)
    mask_draw = ImageDraw.Draw(title_mask)
    mask_draw.rectangle((tx - 8, ty - 8, tx - 8 + mask_width, ty + th + 16), fill=int(255 * opacity))

    ImageDraw.Draw(glow_layer).text((tx, ty), title, font=title_font, fill=(48, 163, 255, int(180 * opacity)))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(9))
    title_layer.alpha_composite(glow_layer)

    draw = ImageDraw.Draw(title_layer)
    draw.text((tx, ty), title, font=title_font, fill=(233, 246, 255, int(255 * opacity)))
    draw.text((tx + 2, ty + 2), title, font=title_font, fill=(97, 219, 255, int(48 * opacity)))
    title_layer.putalpha(Image.composite(title_layer.getchannel("A"), Image.new("L", (WIDTH, HEIGHT), 0), title_mask))
    base.alpha_composite(title_layer)

    if 0.12 < progress < 0.86:
        cursor_x = tx - 8 + mask_width
        pulse = 0.5 + 0.5 * math.sin(progress * math.tau * 4)
        ImageDraw.Draw(base, "RGBA").rounded_rectangle(
            (cursor_x, ty - 10, cursor_x + 3, ty + th + 8),
            radius=2,
            fill=(89, 255, 198, int((70 + 110 * pulse) * opacity)),
        )

    sub_alpha = int(220 * smoothstep(0.36, 0.54, progress) * hold)
    draw_centered(base, subtitle, 184, text_font, (174, 194, 221, sub_alpha))

    close_alpha = int(210 * smoothstep(0.55, 0.72, progress) * hold)
    draw_centered(base, closing, 224, small_font, (112, 255, 210, close_alpha))


def render() -> None:
    ASSETS.mkdir(exist_ok=True)
    frames: list[Image.Image] = []

    for index in range(FRAMES):
        progress = index / FRAMES
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
        fade = clamp(smoothstep(0.0, 0.08, progress) * (1 - smoothstep(0.9, 1.0, progress)))
        draw_background(frame, progress)
        draw_particles(frame, progress, fade)
        draw_signature(frame, progress)

        cover = Image.new("RGBA", (WIDTH, HEIGHT), (9, 14, 23, int(255 * (1 - fade))))
        frame.alpha_composite(cover)
        frames.append(frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))

    output = ASSETS / "meiiie-signature.gif"
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )

    png = ASSETS / "meiiie-signature.png"
    frames[42].convert("RGBA").save(png)
    print(output)
    print(png)


if __name__ == "__main__":
    render()

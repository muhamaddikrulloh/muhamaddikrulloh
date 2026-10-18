
"""
Generate an animated monochrome ASCII portrait SVG.

Features:
- Preserves transparent PNG backgrounds
- Clean, single-color ASCII portrait
- Terminal-style window
- Row-by-row typing animation
- GitHub README compatible (SVG + SMIL)
"""

from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import html
import os
import sys


# ============================================================
# PATH CONFIGURATION
# ============================================================

HERE = os.path.dirname(os.path.abspath(__file__))

SRC = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.path.join(HERE, "..", "source-prepped.png")
)

OUT = (
    sys.argv[2]
    if len(sys.argv) > 2
    else os.path.join(HERE, "..", "dikrulloh-ascii.svg")
)


# ============================================================
# ASCII CONFIGURATION
# ============================================================

COLS = int(os.environ.get("COLS", 180))

ART_W_TARGET = 800
CELL_W = ART_W_TARGET / COLS
CELL_H = CELL_W * 15 / 8

ROWS = round(COLS * 8 / 15)

RAMP = " .`:-=+*cs#%@"

CONTRAST = 1.15
BRIGHTNESS = 1.10
GAMMA = 1.10
SHARPEN = True

WHITE_FLOOR = 0.95
ALPHA_THRESHOLD = 100


# ============================================================
# TERMINAL LAYOUT
# ============================================================

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30

ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H

CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD


# ============================================================
# COLORS
# ============================================================

BG = "#0D1117"
BG2 = "#111722"

FRAME = "#30363D"
TITLE_TEXT = "#8B949E"

INK = "#C9D1D9"
CURSOR = "#C9D1D9"

DOT_COLORS = ["#FF5F56", "#FFBD2E", "#27C93F"]


# ============================================================
# TERMINAL IDENTITY
# ============================================================

USERNAME = "dikrulloh"
FULL_NAME = "Muhamad Dikrulloh"

HEADER_TEXT = f"{USERNAME}@github: ~$ ./portrait.sh"
STATUS_PREFIX = f"{USERNAME}@github:~$ whoami "
STATUS_TEXT = STATUS_PREFIX + FULL_NAME


# ============================================================
# ANIMATION
# ============================================================

TOTAL_DURATION = 5.8

ROW_DUR = TOTAL_DURATION / ROWS
STAGGER = ROW_DUR

STATIC = bool(os.environ.get("STATIC"))


# ============================================================
# IMAGE PROCESSING
# ============================================================

if not os.path.isfile(SRC):
    raise FileNotFoundError(
        f"Source image not found: {SRC}"
    )

# Preserve the alpha channel.
image = Image.open(SRC).convert("RGBA")

alpha = image.getchannel("A")
gray = ImageOps.grayscale(image)

if SHARPEN:
    gray = gray.filter(
        ImageFilter.UnsharpMask(
            radius=2,
            percent=140,
            threshold=2
        )
    )

gray = ImageEnhance.Brightness(gray).enhance(BRIGHTNESS)
gray = ImageEnhance.Contrast(gray).enhance(CONTRAST)

gray = gray.resize(
    (COLS, ROWS),
    Image.Resampling.LANCZOS
)

alpha = alpha.resize(
    (COLS, ROWS),
    Image.Resampling.LANCZOS
)

pixels = gray.load()
mask = alpha.load()


# ============================================================
# ASCII CONVERSION
# ============================================================

rows_txt = []

for y in range(ROWS):
    chars = []

    for x in range(COLS):

        # Completely hide transparent background.
        if mask[x, y] < ALPHA_THRESHOLD:
            chars.append(" ")
            continue

        lum = pixels[x, y] / 255.0
        lum = pow(lum, GAMMA)

        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue

        index = round(
            (1.0 - lum) * (len(RAMP) - 1)
        )

        index = max(
            0,
            min(index, len(RAMP) - 1)
        )

        chars.append(RAMP[index])

    rows_txt.append("".join(chars))


# ============================================================
# SVG HELPERS
# ============================================================

parts = []


def add(value):
    parts.append(value)


def esc(value):
    return html.escape(str(value), quote=True)


# ============================================================
# SVG DOCUMENT
# ============================================================

add(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{CANVAS_W:.0f}" '
    f'height="{CANVAS_H:.0f}" '
    f'viewBox="0 0 {CANVAS_W:.1f} {CANVAS_H:.1f}" '
    f'font-family="Consolas, Menlo, monospace">'
)

# Background gradient
add(
    '<defs>'
    '<linearGradient id="terminal-bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/>'
    f'<stop offset="1" stop-color="{BG}"/>'
    '</linearGradient>'
    '</defs>'
)

# Terminal background
add(
    f'<rect width="{CANVAS_W:.1f}" '
    f'height="{CANVAS_H:.1f}" '
    f'rx="12" fill="url(#terminal-bg)"/>'
)

# Terminal border
add(
    f'<rect x="0.5" y="0.5" '
    f'width="{CANVAS_W - 1:.1f}" '
    f'height="{CANVAS_H - 1:.1f}" '
    f'rx="12" fill="none" '
    f'stroke="{FRAME}" stroke-width="1"/>'
)


# ============================================================
# TITLE BAR
# ============================================================

add(
    f'<line x1="0" y1="{TITLEBAR_H}" '
    f'x2="{CANVAS_W:.1f}" y2="{TITLEBAR_H}" '
    f'stroke="{FRAME}"/>'
)

for index, color in enumerate(DOT_COLORS):
    add(
        f'<circle '
        f'cx="{PAD + index * 16}" '
        f'cy="{TITLEBAR_H / 2}" '
        f'r="5" fill="{color}"/>'
    )

add(
    f'<text x="{CANVAS_W / 2:.1f}" '
    f'y="{TITLEBAR_H / 2 + 4:.1f}" '
    f'fill="{TITLE_TEXT}" '
    f'font-size="12" '
    f'text-anchor="middle">'
    f'{esc(HEADER_TEXT)}'
    '</text>'
)


# ============================================================
# ASCII ART
# ============================================================

art_top = TITLEBAR_H + PAD * 0.35

font_size = CELL_H * 0.86

for row_index, line in enumerate(rows_txt):

    row_y = art_top + row_index * CELL_H

    text_y = row_y + CELL_H * 0.74

    delay = row_index * STAGGER

    safe_line = esc(line)

    row_text = (
        f'<text xml:space="preserve" '
        f'x="{PAD}" '
        f'y="{text_y:.2f}" '
        f'fill="{INK}" '
        f'font-size="{font_size:.2f}" '
        f'textLength="{ART_W:.2f}" '
        f'lengthAdjust="spacing">'
        f'{safe_line}'
        '</text>'
    )

    if STATIC:
        add(row_text)
        continue

    # Reveal each row from left to right.
    clip_id = f"ascii-row-{row_index}"

    add(
        f'<clipPath id="{clip_id}">'
        f'<rect x="{PAD}" '
        f'y="{row_y:.2f}" '
        f'height="{CELL_H:.2f}" '
        f'width="0">'
        f'<animate attributeName="width" '
        f'from="0" to="{ART_W:.2f}" '
        f'begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.3f}s" '
        f'fill="freeze"/>'
        '</rect>'
        '</clipPath>'
    )

    add(
        f'<g clip-path="url(#{clip_id})">'
        f'{row_text}'
        '</g>'
    )

    # Moving block cursor.
    add(
        f'<rect '
        f'y="{row_y + 1:.2f}" '
        f'width="{CELL_W:.2f}" '
        f'height="{max(1, CELL_H - 2):.2f}" '
        f'fill="{CURSOR}" '
        f'opacity="0">'
        f'<animate attributeName="x" '
        f'from="{PAD}" '
        f'to="{PAD + ART_W:.2f}" '
        f'begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.3f}s" '
        f'fill="freeze"/>'
        f'<set attributeName="opacity" '
        f'to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" '
        f'to="0" begin="{delay + ROW_DUR:.3f}s"/>'
        '</rect>'
    )


# ============================================================
# STATUS BAR
# ============================================================

status_line_y = TITLEBAR_H + ART_H + PAD * 0.35

status_y = status_line_y + 19

add(
    f'<line x1="0" '
    f'y1="{status_line_y:.2f}" '
    f'x2="{CANVAS_W:.1f}" '
    f'y2="{status_line_y:.2f}" '
    f'stroke="{FRAME}"/>'
)

add(
    f'<text x="{PAD}" '
    f'y="{status_y:.2f}" '
    f'fill="{TITLE_TEXT}" '
    f'font-size="13">'
    f'{esc(STATUS_PREFIX)}'
    f'<tspan fill="{INK}">{esc(FULL_NAME)}</tspan>'
    '</text>'
)

# Blinking terminal cursor.
# Approximate width for Consolas monospace at 13px.
cursor_x = PAD + len(STATUS_TEXT) * 13 * 0.6

add(
    f'<rect x="{cursor_x:.2f}" '
    f'y="{status_y - 12:.2f}" '
    f'width="8" height="14" '
    f'fill="{INK}">'
    '<animate attributeName="opacity" '
    'values="1;1;0;0" '
    'keyTimes="0;0.5;0.51;1" '
    'dur="1s" '
    'repeatCount="indefinite"/>'
    '</rect>'
)


# ============================================================
# SAVE SVG
# ============================================================

add("</svg>")

svg = "".join(parts)

output_dir = os.path.dirname(os.path.abspath(OUT))
os.makedirs(output_dir, exist_ok=True)

with open(OUT, "w", encoding="utf-8") as file:
    file.write(svg)

print(f"SVG generated: {OUT}")
print(f"Canvas: {CANVAS_W:.0f} x {CANVAS_H:.0f}")
print(f"ASCII grid: {COLS} columns x {ROWS} rows")
print(f"File size: {len(svg):,} bytes")

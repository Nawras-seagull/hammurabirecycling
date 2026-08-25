#!/usr/bin/env python3
"""
Generates branded placeholder images so the static site is fully viewable
before the client drops in real photography from the WP media library.
Every filename below matches the mapping documented in README.md so the
client can drop in a real photo with the SAME filename and nothing else
needs to change in the HTML/CSS.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

OUT = "/home/claude/site/assets/images"
os.makedirs(OUT, exist_ok=True)

# Brand palette
BASALT = (20, 18, 15)
CHAR = (30, 27, 21)
GOLD = (199, 154, 69)
GOLD_DIM = (140, 108, 52)
BRICK = (161, 75, 51)
PARCHMENT = (237, 230, 214)
STEEL = (156, 151, 138)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
def font(size, bold=False):
    path = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    return ImageFont.truetype(path, size)

def mono_font(size):
    return ImageFont.truetype(os.path.join(FONT_DIR, "DejaVuSansMono.ttf"), size)

def noise_bg(w, h, base, variance=6):
    img = Image.new("RGB", (w, h), base)
    px = img.load()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            n = random.randint(-variance, variance)
            c = tuple(max(0, min(255, base[i] + n)) for i in range(3))
            for dy in range(2):
                for dx in range(2):
                    if x+dx < w and y+dy < h:
                        px[x+dx, y+dy] = c
    return img

def diagonal_hatch(draw, w, h, color, spacing=26, width=1):
    for x in range(-h, w, spacing):
        draw.line([(x, 0), (x + h, h)], fill=color, width=width)

def center_text(draw, box, text, fnt, fill, spacing=0):
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = x0 + (x1-x0-tw)/2 - bbox[0]
    y = y0 + (y1-y0-th)/2 - bbox[1]
    draw.text((x, y), text, font=fnt, fill=fill)

def gate_glyph(draw, cx, cy, s, color, width=4):
    # simple two-pier + lintel "gate" mark
    draw.line([(cx-s, cy+s), (cx-s, cy-s*0.2)], fill=color, width=width)
    draw.line([(cx+s, cy+s), (cx+s, cy-s*0.2)], fill=color, width=width)
    draw.line([(cx-s*1.15, cy-s*0.2), (cx+s*1.15, cy-s*0.2)], fill=color, width=width)
    draw.line([(cx-s*1.3, cy-s*0.45), (cx+s*1.3, cy-s*0.45)], fill=color, width=int(width*0.7))

def save(img, name, quality=84):
    base = os.path.join(OUT, name)
    img.save(base, quality=quality)
    webp = os.path.splitext(base)[0] + ".webp"
    img.save(webp, "WEBP", quality=quality)
    print("wrote", name, "+ .webp")

def process_image(name, w, h, label, sublabel, seed):
    random.seed(seed)
    img = noise_bg(w, h, CHAR, 5)
    draw = ImageDraw.Draw(img, "RGBA")
    diagonal_hatch(draw, w, h, (255, 255, 255, 8), spacing=40, width=1)
    # gold corner frame
    m = 24
    draw.rectangle([m, m, w-m, h-m], outline=(*GOLD, 140), width=2)
    gate_glyph(draw, w/2, h*0.40, min(w, h)*0.16, GOLD)
    center_text(draw, (0, h*0.62, w, h*0.72), label, font(int(h*0.075), bold=True), PARCHMENT)
    center_text(draw, (0, h*0.74, w, h*0.80), sublabel, mono_font(int(h*0.032)), GOLD)
    img = img.filter(ImageFilter.GaussianBlur(0.3))
    save(img, name)

def circle_image(name, size, label, seed):
    random.seed(seed)
    img = noise_bg(size, size, BASALT, 5)
    draw = ImageDraw.Draw(img, "RGBA")
    cx, cy = size/2, size/2
    r = size*0.46
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(*GOLD, 200), width=6)
    r2 = size*0.36
    draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], fill=(*CHAR, 255))
    gate_glyph(draw, cx, cy-size*0.04, size*0.09, GOLD, width=3)
    center_text(draw, (0, size*0.58, size, size*0.7), label, font(int(size*0.058), bold=True), PARCHMENT)
    save(img, name)

def photo_placeholder(name, w, h, label, sublabel, seed):
    random.seed(seed)
    img = noise_bg(w, h, BASALT, 6)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(6):
        y = int(h * (0.15 + i*0.14))
        draw.line([(0, y), (w, y+30)], fill=(*BRICK, 18), width=40)
    m = 20
    draw.rectangle([m, m, w-m, h-m], outline=(*GOLD_DIM, 160), width=2)
    center_text(draw, (0, h*0.44, w, h*0.56), label, font(int(h*0.07), bold=True), PARCHMENT)
    center_text(draw, (0, h*0.58, w, h*0.66), sublabel, mono_font(int(h*0.028)), GOLD)
    save(img, name)

def og_image():
    w, h = 1200, 630
    img = noise_bg(w, h, BASALT, 5)
    draw = ImageDraw.Draw(img, "RGBA")
    m = 30
    draw.rectangle([m, m, w-m, h-m], outline=(*GOLD, 180), width=3)
    gate_glyph(draw, w/2, h*0.38, 90, GOLD, width=6)
    center_text(draw, (0, h*0.55, w, h*0.68), "HAMMURABI GOLDEN GATE", font(58, bold=True), PARCHMENT)
    center_text(draw, (0, h*0.70, w, h*0.80), "ADVANCED TIRE RECYCLING FOR A BETTER TOMORROW", mono_font(20), GOLD)
    save(img.convert("RGB"), "og-cover.webp", quality=88)

def favicon_set():
    size = 512
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rounded_rectangle([0,0,size,size], radius=64, fill=(*BASALT, 255))
    gate_glyph(draw, size/2, size*0.56, size*0.26, GOLD, width=22)
    img.save(os.path.join(OUT, "favicon-512.png"))
    img.resize((192,192), Image.LANCZOS).save(os.path.join(OUT, "favicon-192.png"))
    img.resize((32,32), Image.LANCZOS).save(os.path.join(OUT, "favicon-32.png"))
    img.resize((180,180), Image.LANCZOS).save(os.path.join(OUT, "apple-touch-icon.png"))

# --- Process (4 steps) ---
process_image("collecting.webp", 1200, 900, "Collection & Sorting", "STAGE 01 — INTAKE", 1)
process_image("shreding.webp",   1200, 900, "Shredding",             "STAGE 02 — REDUCTION", 2)
process_image("grinding.webp",   1200, 900, "Grinding & Granulation","STAGE 03 — REFINEMENT", 3)
process_image("gg.webp",         1200, 900, "Product Creation",      "STAGE 04 — OUTPUT", 4)

# --- Products (circular) ---
circle_image("CirclePhoto_SmartMIX.webp", 800, "Asphalts", 5)
circle_image("CirclePhoto_Crumb.webp",    800, "Crumb", 6)
circle_image("CirclePhoto_TDF.webp",      800, "Tire Derived Fuel", 7)

# --- About page photography ---
photo_placeholder("unnamed.webp",   1200, 900, "Our Mission", "FACTORY FLOOR — BAGHDAD", 8)
photo_placeholder("unnamed-1.webp", 1200, 900, "Our Vision",  "REGIONAL BENCHMARK", 9)
photo_placeholder("hero-factory.webp", 1600, 1000, "Hammurabi Golden Gate", "TIRE RECYCLING FACILITY — IRAQ", 10)
photo_placeholder("about-hero.webp", 1600, 900, "About Hammurabi Golden Gate", "OUR STORY", 11)

# --- Misc ---
og_image()
favicon_set()

print("Done.")

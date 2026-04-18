"""
Generate synthetic sample data for testing the app without a real PPTX file.

Creates data/people.json and data/images/ with 20 colour-swatch "portraits".

Usage:
    python generate_sample_data.py
"""

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SAMPLE_NAMES = [
    "Alice Johnson", "Bob Martinez", "Carol White", "David Lee",
    "Eve Thompson", "Frank Garcia", "Grace Hall", "Henry Clark",
    "Iris Lewis", "Jack Robinson", "Karen Walker", "Liam Harris",
    "Mia Young", "Noah Allen", "Olivia King", "Paul Wright",
    "Quinn Scott", "Rachel Green", "Sam Turner", "Tina Baker",
]

COLOURS = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#34495e", "#e91e63", "#00bcd4",
    "#8bc34a", "#ff5722", "#607d8b", "#795548", "#ff9800",
    "#673ab7", "#4caf50", "#f44336", "#2196f3", "#009688",
]


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def make_portrait(name: str, color: str, size: int = 300) -> Image.Image:
    img = Image.new("RGB", (size, size), hex_to_rgb(color))
    draw = ImageDraw.Draw(img)

    # Draw a simple face silhouette
    # Head circle
    margin = size // 8
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(255, 255, 255, 80))

    # Initials
    initials = "".join(part[0].upper() for part in name.split() if part)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 3)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((size - text_w) / 2, (size - text_h) / 2),
        initials,
        fill=hex_to_rgb(color),
        font=font,
    )
    return img


def main() -> None:
    data_dir = Path("data")
    images_dir = data_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    people = []
    colours = COLOURS.copy()
    random.shuffle(colours)

    for i, name in enumerate(SAMPLE_NAMES):
        colour = colours[i % len(colours)]
        img = make_portrait(name, colour)

        safe = name.replace(" ", "_")
        filename = f"{safe}.png"
        img.save(images_dir / filename)

        people.append({"name": name, "image_path": f"images/{filename}"})
        print(f"Created: {name}")

    with open(data_dir / "people.json", "w", encoding="utf-8") as f:
        json.dump(people, f, indent=2)

    print(f"\nSample data written to data/ ({len(people)} people).")
    print("Run  streamlit run app.py  to start the trainer.")


if __name__ == "__main__":
    main()

"""Generate style-card thumbnails with the app's own algorithms.

Usage (from backend/):  python scripts/make_thumbnails.py
"""
import os
import sys

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.services.styles import SKETCH_STYLES  # noqa: E402
from app.utils.sample import make_sample_image  # noqa: E402

OUT = os.path.join(os.path.dirname(ROOT), "frontend", "public", "styles")
W, H = 320, 240


def main():
    os.makedirs(OUT, exist_ok=True)
    sample = make_sample_image(W, H)
    cv2.imwrite(os.path.join(OUT, "original.jpg"), sample, [cv2.IMWRITE_JPEG_QUALITY, 85])
    for name, generate in SKETCH_STYLES.items():
        result = generate(sample, W, H, {})
        cv2.imwrite(os.path.join(OUT, f"{name}.jpg"), result, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print("wrote", name)


if __name__ == "__main__":
    main()

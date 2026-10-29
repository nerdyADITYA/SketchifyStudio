import cv2
import numpy as np

from ._common import auto_canny, finish, level, odd, prepare_gray, scale_for, thicken


def generate(image, width, height, options=None):
    """Minimal clean outlines: heavy smoothing, Canny, small-component removal, line joining."""
    gray = prepare_gray(image, width, height)
    s = scale_for(width, height)

    detail = level(options, "detail")
    thickness = level(options, "line_thickness")
    intensity = level(options, "intensity")

    smooth = cv2.medianBlur(gray, odd(5 * s, 5))
    smooth = cv2.bilateralFilter(smooth, 9, 60, 60)
    smooth = cv2.GaussianBlur(smooth, (0, 0), 1.5 * s)

    edges = auto_canny(smooth, scale=1.8 - 1.0 * detail)

    # Drop small, isolated fragments; the minimum size shrinks as detail rises.
    # Edges are ~1 px wide, so a fragment's area grows with its length (~s), not with s squared.
    min_area = (15.0 + 60.0 * (1.0 - detail)) * s
    count, labels, stats, _ = cv2.connectedComponentsWithStats(edges, connectivity=8)
    keep = np.zeros(count, dtype=np.uint8)
    keep[1:] = (stats[1:, cv2.CC_STAT_AREA] >= min_area).astype(np.uint8) * 255
    cleaned = keep[labels]

    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    cleaned = thicken(cleaned, max(1, int(round((1.0 + 2.0 * thickness) * s))))
    cleaned = cv2.GaussianBlur(cleaned, (0, 0), 0.6).astype(np.float32) / 255.0

    out = 255.0 * (1.0 - np.clip(cleaned * (0.7 + 0.6 * intensity), 0, 1))
    return finish(out)

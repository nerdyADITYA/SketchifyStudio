import cv2
import numpy as np

from ._common import adjust_contrast, auto_canny, finish, level, prepare_gray, scale_for, thicken


def generate(image, width, height, options=None):
    """Bold black outlines on white paper: Canny + dilation + morphological closing."""
    gray = prepare_gray(image, width, height)
    s = scale_for(width, height)

    detail = level(options, "detail")
    thickness = level(options, "line_thickness")
    intensity = level(options, "intensity")
    contrast = level(options, "contrast")

    blurred = cv2.GaussianBlur(gray, (0, 0), 1.0 * s + 0.5)
    edges = auto_canny(blurred, scale=1.5 - 0.8 * detail)

    size = max(1, int(round((1.0 + 4.0 * thickness) * s)))
    edges = thicken(edges, size)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    edges = cv2.GaussianBlur(edges, (0, 0), 0.7)

    ink = edges.astype(np.float32) / 255.0 * (0.6 + 0.8 * intensity)
    out = 255.0 * (1.0 - np.clip(ink, 0, 1))
    out = adjust_contrast(out, 0.7 + 0.6 * contrast)
    return finish(out)

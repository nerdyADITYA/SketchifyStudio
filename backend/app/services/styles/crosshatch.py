import cv2
import numpy as np

from ._common import auto_canny, finish, level, prepare_gray, scale_for

# (brightness threshold, hatch angle in degrees): darker regions receive more layers.
LAYERS = ((185, 45), (140, 135), (95, 0), (55, 90))


def _hatch_mask(height, width, angle_deg, spacing, thickness):
    """Boolean mask of parallel, slightly wavy lines at the given angle."""
    theta = np.deg2rad(angle_deg)
    x = np.arange(width, dtype=np.float32)[None, :]
    y = np.arange(height, dtype=np.float32)[:, None]
    u = x * np.float32(np.cos(theta)) + y * np.float32(np.sin(theta))
    u = u + (1.2 * np.sin(y * 0.021 + angle_deg)).astype(np.float32)
    return np.mod(u, np.float32(spacing)) < thickness


def generate(image, width, height, options=None):
    """Directional hatching whose density follows brightness, combined with Canny edges."""
    gray = prepare_gray(image, width, height)
    s = scale_for(width, height)

    shading = level(options, "shading")
    thickness = level(options, "line_thickness")
    intensity = level(options, "intensity")
    contrast = level(options, "contrast")
    detail = level(options, "detail")

    tone = cv2.GaussianBlur(gray, (0, 0), 1.5 * s).astype(np.float32)
    tone = (tone - 128.0) * (0.7 + 0.7 * contrast) + 128.0

    spacing = max(3.0, (8.0 - 3.5 * shading) * s)
    line_width = max(1.0, spacing * (0.18 + 0.25 * thickness))
    shift = (intensity - 0.5) * 70.0

    canvas = np.full(gray.shape, 255, dtype=np.uint8)
    for threshold, angle in LAYERS:
        dark = tone < (threshold + shift)
        canvas[dark & _hatch_mask(height, width, angle, spacing, line_width)] = 25

    canvas = cv2.GaussianBlur(canvas, (0, 0), 0.6)

    edges = auto_canny(cv2.GaussianBlur(gray, (0, 0), 1.2 * s + 0.4), scale=1.6 - 0.9 * detail)
    edges = cv2.GaussianBlur(edges, (0, 0), 0.6)
    out = np.minimum(canvas.astype(np.float32), 255.0 - 0.9 * edges.astype(np.float32))
    return finish(out)

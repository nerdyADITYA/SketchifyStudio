import cv2
import numpy as np

from app.services.image_service import resize_image

from ._common import adjust_contrast, finish, level, odd, prepare_gray, scale_for, thicken, wants_color

SMOOTHING_MAX_SIDE = 1600


def _smooth(img, passes):
    """Edge-preserving smoothing (gray or BGR), run on a capped working size for speed."""
    h, w = img.shape[:2]
    factor = min(1.0, SMOOTHING_MAX_SIDE / max(h, w))
    work = cv2.resize(img, (max(1, int(w * factor)), max(1, int(h * factor))), interpolation=cv2.INTER_AREA) \
        if factor < 1.0 else img
    for _ in range(passes):
        work = cv2.bilateralFilter(work, 9, 40, 7)
    if factor < 1.0:
        work = cv2.resize(work, (w, h), interpolation=cv2.INTER_LINEAR)
    return work


def generate(image, width, height, options=None):
    """Stylised drawing: bilateral smoothing, posterised tones and strong adaptive-threshold outlines.

    With colour mode on, the posterised regions keep the photo's colours.
    """
    gray = prepare_gray(image, width, height)
    s = scale_for(width, height)

    detail = level(options, "detail")
    thickness = level(options, "line_thickness")
    intensity = level(options, "intensity")
    contrast = level(options, "contrast")

    bands = 3 + int(round(detail * 6))
    step = 256.0 / bands

    line_source = cv2.medianBlur(gray, odd(5 * s, 5))
    outlines = cv2.adaptiveThreshold(
        line_source, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, odd(11 * s, 9), 4 + 4 * (1 - detail)
    )
    lines = thicken(255 - outlines, max(1, int(round((1.0 + 2.5 * thickness) * s))))
    lines = cv2.GaussianBlur(lines, (0, 0), 0.6).astype(np.float32) / 255.0
    line_mask = 1.0 - np.clip(lines * (0.6 + 0.8 * intensity), 0, 0.95)

    if wants_color(options):
        strength = (options or {}).get("color_strength", 100) / 100.0
        smooth = _smooth(resize_image(image, width, height), passes=3).astype(np.float32)
        color_step = 256.0 / (bands + 3)  # extra levels per channel keep hues recognisable
        flat = (np.floor(smooth / color_step) + 0.5) * color_step
        hsv = cv2.cvtColor(np.clip(flat, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] = np.clip(hsv[..., 1] * 1.2, 0, 255)
        flat = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        luma = flat.mean(axis=2, keepdims=True)
        flat = luma + (flat - luma) * strength  # strength fades colour toward the gray version
        out = adjust_contrast(flat * line_mask[..., None], 0.9 + 0.4 * contrast, pivot=140.0)
        return finish(out)

    smooth = _smooth(gray, passes=3).astype(np.float32)
    tones = (np.floor(smooth / step) + 0.5) * step
    tones = 255.0 * np.power(np.clip(tones / 255.0, 0, 1), 0.6)  # lighten towards paper white
    out = adjust_contrast(tones * line_mask, 0.8 + 0.6 * contrast, pivot=150.0)
    return finish(out)

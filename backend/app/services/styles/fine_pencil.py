import cv2
import numpy as np

from ._common import adjust_contrast, auto_canny, dodge, finish, level, prepare_gray, scale_for


def generate(image, width, height, options=None):
    """Delicate sketch: thin Canny lines over very light dodge shading."""
    gray = prepare_gray(image, width, height)
    s = scale_for(width, height)

    detail = level(options, "detail")
    intensity = level(options, "intensity")
    shading = level(options, "shading")
    contrast = level(options, "contrast")

    denoised = cv2.bilateralFilter(gray, 5, 35, 35)
    denoised = cv2.GaussianBlur(denoised, (0, 0), 0.6 * s + 0.3)

    edges = auto_canny(denoised, scale=1.4 - 0.8 * detail)
    lines = cv2.GaussianBlur(edges, (0, 0), 0.6).astype(np.float32) / 255.0

    shade = dodge(gray, sigma=10.0 * s).astype(np.float32)
    shade = 255.0 - (255.0 - shade) * (0.15 + 0.4 * shading)

    out = shade * (1.0 - np.clip(lines * (0.5 + 0.7 * intensity), 0, 0.92))
    out = adjust_contrast(out, 0.8 + 0.5 * contrast, pivot=220.0)
    return finish(out)

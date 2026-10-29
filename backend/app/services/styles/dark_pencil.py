import cv2
import numpy as np

from ._common import adjust_contrast, dodge, finish, level, prepare_gray, scale_for


def generate(image, width, height, options=None):
    """Bold pencil: dodge pipeline, darkened mid-tones and gradient-driven strokes."""
    gray = prepare_gray(image, width, height)
    s = scale_for(width, height)

    intensity = level(options, "intensity")
    shading = level(options, "shading")
    contrast = level(options, "contrast")
    detail = level(options, "detail")

    base = dodge(gray, sigma=4.0 * s * (0.5 + shading)).astype(np.float32)

    # Gamma > 1 darkens mid-tones while pure highlights stay white.
    gamma = 1.0 + 1.6 * intensity
    base = 255.0 * np.power(base / 255.0, gamma)

    smooth = cv2.GaussianBlur(gray, (0, 0), 0.8 * s + 0.4).astype(np.float32)
    gx = cv2.Sobel(smooth, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(smooth, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)
    magnitude /= max(float(np.percentile(magnitude, 99)), 1.0)
    strokes = np.clip(magnitude, 0, 1)
    base -= 140.0 * (0.4 + 0.8 * detail) * strokes

    out = adjust_contrast(base, 1.0 + 0.6 * contrast, pivot=150.0)
    return finish(out)

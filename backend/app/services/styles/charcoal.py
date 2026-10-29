import cv2
import numpy as np

from ._common import finish, level, odd, prepare_gray, scale_for


def generate(image, width, height, options=None):
    """Charcoal: CLAHE + posterised tones blended with adaptive-threshold masses and paper grain."""
    gray = prepare_gray(image, width, height)
    s = scale_for(width, height)

    intensity = level(options, "intensity")
    shading = level(options, "shading")
    contrast = level(options, "contrast")
    detail = level(options, "detail")

    clahe = cv2.createCLAHE(clipLimit=1.5 + 4.0 * contrast, tileGridSize=(8, 8)).apply(gray)
    smooth = cv2.bilateralFilter(clahe, 7, 50, 50)
    smooth = cv2.GaussianBlur(smooth, (0, 0), 1.2 * s)

    darkness = 1.0 - smooth.astype(np.float32) / 255.0
    levels = 4 + int(round(detail * 4))
    quantized = np.floor(darkness * levels) / levels
    quantized = cv2.GaussianBlur(quantized, (0, 0), 1.5 * s)

    masses = cv2.adaptiveThreshold(
        cv2.medianBlur(gray, 5),
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        odd(25 * s, 11),
        8,
    )
    masses = cv2.GaussianBlur(1.0 - masses.astype(np.float32) / 255.0, (0, 0), 1.2 * s)

    tone = 0.65 * quantized + 0.35 * masses
    tone = np.clip((tone - 0.2) / 0.8, 0, 1)  # keep light areas as bare paper

    # Shadow intensity: lower exponent pushes tones darker.
    tone = np.power(np.clip(tone, 0, 1), 1.3 - 0.6 * shading)

    rng = np.random.default_rng(7)
    grain = cv2.GaussianBlur(rng.normal(0.0, 1.0, tone.shape).astype(np.float32), (0, 0), 0.7)
    tone = tone + grain * 0.05 * np.clip(tone * 3.0, 0, 1)

    tone = np.clip(tone * (0.6 + 0.9 * intensity), 0, 1)
    return finish(250.0 - 250.0 * tone)

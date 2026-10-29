"""Helpers shared by the sketch style modules."""
import cv2
import numpy as np

from app.services.image_service import resize_image


def prepare_gray(image, width, height):
    """Validate, resize and convert to grayscale."""
    if image is None or image.size == 0:
        raise ValueError("Invalid image data.")
    resized = resize_image(image, width, height)
    if resized.ndim == 2:
        return resized
    return cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)


def level(options, key, default=0.5):
    """Return an option as a 0..1 float."""
    value = (options or {}).get(key)
    if value is None:
        return default
    return float(np.clip(value / 100.0, 0.0, 1.0))


def scale_for(width, height):
    """Size factor so that strokes look similar regardless of resolution."""
    return float(np.clip(np.sqrt(width * height) / 1000.0, 0.35, 4.0))


def odd(value, minimum=3):
    n = max(int(round(value)), minimum)
    return n if n % 2 == 1 else n + 1


def dodge(gray, sigma):
    """Classic invert -> blur -> invert -> colour-dodge pencil effect."""
    inverted = 255 - gray
    blurred = cv2.GaussianBlur(inverted, (0, 0), sigmaX=max(sigma, 0.5))
    inverted_blur = 255 - blurred
    return cv2.divide(gray, np.maximum(inverted_blur, 1), scale=256)


def auto_canny(gray, scale=1.0):
    """Canny with thresholds derived from the image's own gradient distribution.

    Median-brightness thresholds fail on bright or dark photos, so the high
    threshold follows the 92nd percentile of the Sobel gradient magnitude.
    Lower `scale` keeps more edges.
    """
    # Stretch the tonal range first so dark or low-contrast photos still yield edges.
    low_p, high_p = np.percentile(gray, (1, 99))
    gain = 255.0 / max(float(high_p - low_p), 40.0)
    gray = np.clip((gray.astype(np.float32) - low_p) * gain, 0, 255).astype(np.uint8)

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)
    high = float(np.clip(np.percentile(magnitude, 92) * scale, 90.0, 500.0))
    return cv2.Canny(gray, 0.4 * high, high, L2gradient=True)


def adjust_contrast(img, factor, pivot=128.0):
    out = (img.astype(np.float32) - pivot) * factor + pivot
    return out


def finish(img):
    return np.clip(img, 0, 255).astype(np.uint8)


def wants_color(options):
    return (options or {}).get("color_mode") == "color"


def colorize(image, width, height, sketch, strength=1.0):
    """Tint a grayscale sketch with the photo's colours (multiply blend).

    Lines and shading stay dark; paper-white areas take on a lightened,
    slightly saturated version of the original colours.
    """
    color = resize_image(image, width, height)
    color = cv2.bilateralFilter(color, 7, 40, 7) if width * height <= 4_000_000 else color
    hsv = cv2.cvtColor(color, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.25, 0, 255)
    hsv[..., 2] = 255.0 * np.power(hsv[..., 2] / 255.0, 0.55)
    tint = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) / 255.0
    tint = 1.0 - strength * (1.0 - tint)
    return finish(sketch.astype(np.float32)[..., None] * tint)


def thicken(mask, size):
    if size <= 1:
        return mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    return cv2.dilate(mask, kernel)

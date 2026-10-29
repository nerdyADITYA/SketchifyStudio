import cv2
import numpy as np

from app.errors import ApiError
from app.services.styles import SKETCH_STYLES
from app.services.styles._common import colorize, wants_color


class ProcessingError(RuntimeError):
    """Raised when a style returns an unusable image."""


def generate_sketch(image: np.ndarray, style: str, width: int, height: int, options: dict | None) -> np.ndarray:
    generator = SKETCH_STYLES.get(style)
    if generator is None:
        raise ApiError(422, f"Unknown sketch style '{style}'.", "invalid_style")
    options = options or {}
    result = generator(image, width, height, options)
    # Styles that cannot produce colour themselves are tinted with the photo's colours.
    if result.ndim == 2 and wants_color(options):
        result = colorize(image, width, height, result, options.get("color_strength", 100) / 100.0)
    validate_result(result, width, height)
    return result


def validate_result(result, width: int, height: int) -> None:
    if not isinstance(result, np.ndarray) or result.dtype != np.uint8:
        raise ProcessingError("Style returned an invalid image array.")
    if result.ndim not in (2, 3) or (result.ndim == 3 and result.shape[2] != 3):
        raise ProcessingError("Style returned an unexpected channel layout.")
    if result.shape[:2] != (height, width):
        raise ProcessingError("Style returned an image with the wrong dimensions.")


def encode_image(image: np.ndarray, fmt: str, quality: int) -> tuple[bytes, str]:
    """Encode to PNG (lossless) or JPEG. Returns the bytes and MIME type."""
    if fmt == "png":
        ok, buffer = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 6])
        media_type = "image/png"
    elif fmt == "jpg":
        ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
        media_type = "image/jpeg"
    else:
        raise ApiError(422, "Output format must be 'png' or 'jpg'.", "invalid_format")
    if not ok:
        raise ProcessingError("Failed to encode the result.")
    return buffer.tobytes(), media_type

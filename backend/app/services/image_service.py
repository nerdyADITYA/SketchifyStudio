import io
import warnings

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import Settings
from app.errors import ApiError
from app.utils.validators import validate_input_dimensions

EXPECTED_FORMAT = {"image/jpeg": "JPEG", "image/png": "PNG"}


def decode_image(data: bytes, content_type: str, settings: Settings) -> np.ndarray:
    """Verify the upload with Pillow and return an 8-bit BGR OpenCV image."""
    if not data:
        raise ApiError(422, "The uploaded file is empty.", "empty_file")

    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    # Pixel limits are enforced explicitly below, before any pixel data is decoded.
    warnings.simplefilter("ignore", Image.DecompressionBombWarning)
    try:
        with Image.open(io.BytesIO(data)) as probe:
            actual_format = probe.format
            width, height = probe.size
            frames = getattr(probe, "n_frames", 1)
            probe.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise ApiError(422, "The uploaded file is not a valid image.", "invalid_image") from None

    if actual_format not in ("JPEG", "PNG"):
        raise ApiError(415, "Only JPG, JPEG, and PNG files are supported.", "unsupported_format")
    if actual_format != EXPECTED_FORMAT.get(content_type.lower()):
        raise ApiError(415, "The file contents do not match the declared image type.", "type_mismatch")
    if frames > 1:
        raise ApiError(422, "Animated or multi-frame images are not supported.", "animated_image")

    validate_input_dimensions(width, height, settings)

    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            img.load()
            rgb = _flatten_to_rgb(img)
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise ApiError(422, "The uploaded image is corrupted.", "invalid_image") from None

    array = np.asarray(rgb, dtype=np.uint8)
    return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)


def _flatten_to_rgb(img: Image.Image) -> Image.Image:
    """Normalise every supported mode to RGB, compositing transparency on white."""
    has_alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
    if has_alpha:
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")
    if img.mode in ("I;16", "I;16L", "I;16B", "I"):
        arr = np.asarray(img, dtype=np.float32)
        scale = 255.0 / 65535.0 if arr.max() > 255 else 1.0
        return Image.fromarray(np.clip(arr * scale, 0, 255).astype(np.uint8)).convert("RGB")
    return img.convert("RGB")


def resize_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize with INTER_AREA when shrinking and INTER_CUBIC when enlarging."""
    if image is None or image.size == 0:
        raise ValueError("Invalid image data.")
    h, w = image.shape[:2]
    if (w, h) == (width, height):
        return image.copy()
    shrinking = width < w or height < h
    interpolation = cv2.INTER_AREA if shrinking else cv2.INTER_CUBIC
    return cv2.resize(image, (width, height), interpolation=interpolation)

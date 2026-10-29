import json
import os
import re

from pydantic import ValidationError

from app.config import Settings
from app.errors import ApiError
from app.schemas import StyleOptions

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
OUTPUT_FORMATS = {"png", "jpg"}
MIN_QUALITY = 10
MAX_QUALITY = 100


def validate_upload_metadata(filename: str | None, content_type: str | None) -> None:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ApiError(415, "Only JPG, JPEG, and PNG files are supported.", "unsupported_format")
    if (content_type or "").lower() not in ALLOWED_MIME_TYPES:
        raise ApiError(415, "Please upload a valid JPG or PNG image.", "unsupported_format")


def parse_bool(value: str | None, name: str) -> bool:
    text = (value or "").strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    raise ApiError(400, f"'{name}' must be true or false.", "invalid_parameter")


def parse_int(value: str | None, name: str) -> int:
    try:
        text = (value or "").strip()
        if not re.fullmatch(r"-?\d+", text):
            raise ValueError
        return int(text)
    except ValueError:
        raise ApiError(400, f"'{name}' must be an integer.", "invalid_parameter") from None


def validate_output_format(value: str) -> str:
    fmt = (value or "").strip().lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt not in OUTPUT_FORMATS:
        raise ApiError(422, "Output format must be 'png' or 'jpg'.", "invalid_format")
    return fmt


def validate_quality(value: str | None) -> int:
    quality = parse_int(value if value not in (None, "") else "90", "quality")
    if not MIN_QUALITY <= quality <= MAX_QUALITY:
        raise ApiError(422, f"Quality must be between {MIN_QUALITY} and {MAX_QUALITY}.", "invalid_quality")
    return quality


def parse_options(raw: str | None) -> dict:
    if raw is None or raw.strip() == "":
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ApiError(400, "'options' must be valid JSON.", "invalid_options") from None
    if not isinstance(data, dict):
        raise ApiError(400, "'options' must be a JSON object.", "invalid_options")
    try:
        return StyleOptions(**data).model_dump()
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"]) or "options"
        raise ApiError(422, f"Invalid style option '{field}': {first['msg']}.", "invalid_options") from None


def validate_input_dimensions(width: int, height: int, settings: Settings) -> None:
    if width < settings.min_image_width or height < settings.min_image_height:
        raise ApiError(
            422,
            f"Image is too small. Minimum size is {settings.min_image_width} x {settings.min_image_height} px.",
            "image_too_small",
        )
    if (
        width > settings.max_image_width
        or height > settings.max_image_height
        or width * height > settings.max_image_pixels
    ):
        raise ApiError(422, "Image dimensions exceed the supported limits.", "image_too_large")


def resolve_output_dimensions(
    in_width: int,
    in_height: int,
    width: int,
    height: int,
    preserve_aspect_ratio: bool,
    settings: Settings,
) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        raise ApiError(422, "Output width and height must be positive integers.", "invalid_dimensions")
    if preserve_aspect_ratio:
        height = round(width / in_width * in_height)
    if width < settings.min_output_width or height < settings.min_output_height:
        raise ApiError(
            422,
            f"Output size must be at least {settings.min_output_width} x {settings.min_output_height} px.",
            "invalid_dimensions",
        )
    if (
        width > settings.max_output_width
        or height > settings.max_output_height
        or width * height > settings.max_output_pixels
    ):
        raise ApiError(422, "Output dimensions exceed the supported limits.", "invalid_dimensions")
    return width, height


def sanitize_stem(filename: str | None) -> str:
    stem = os.path.splitext(os.path.basename(filename or ""))[0]
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_")[:60]
    return stem or "image"

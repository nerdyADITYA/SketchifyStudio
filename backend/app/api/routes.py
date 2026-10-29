import asyncio
import logging
import time

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import Response

from app.config import get_settings
from app.errors import ApiError
from app.schemas import HealthResponse
from app.services.image_service import decode_image
from app.services.sketch_service import ProcessingError, encode_image, generate_sketch
from app.services.styles import SKETCH_STYLES
from app.utils.validators import (
    parse_bool,
    parse_int,
    parse_options,
    resolve_output_dimensions,
    sanitize_stem,
    validate_output_format,
    validate_quality,
    validate_upload_metadata,
)

logger = logging.getLogger("sketchify")
router = APIRouter(prefix="/api")

QUEUE_WAIT_SECONDS = 5


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@router.get("/styles")
async def styles():
    return {"styles": list(SKETCH_STYLES)}


async def _run_limited(request: Request, fn):
    """Run blocking work in a thread, bounded by a concurrency limit and a timeout."""
    settings = get_settings()
    state = request.app.state
    if getattr(state, "job_semaphore", None) is None:
        state.job_semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)
    semaphore = state.job_semaphore

    try:
        await asyncio.wait_for(semaphore.acquire(), QUEUE_WAIT_SECONDS)
    except asyncio.TimeoutError:
        raise ApiError(503, "The server is busy. Please try again shortly.", "busy") from None

    future = asyncio.get_running_loop().run_in_executor(None, fn)

    def _release(done):
        if not done.cancelled():
            done.exception()  # mark retrieved so late failures do not warn
        semaphore.release()

    future.add_done_callback(_release)
    try:
        return await asyncio.wait_for(asyncio.shield(future), settings.processing_timeout_seconds)
    except asyncio.TimeoutError:
        raise ApiError(504, "Processing took too long.", "timeout") from None


@router.post("/sketch")
async def create_sketch(
    request: Request,
    file: UploadFile = File(...),
    style: str = Form(...),
    width: str = Form(...),
    height: str = Form(...),
    format: str = Form(...),
    preserve_aspect_ratio: str = Form("true"),
    quality: str = Form("90"),
    options: str | None = Form(None),
):
    settings = get_settings()

    # Cheap parameter checks first, before touching the image.
    validate_upload_metadata(file.filename, file.content_type)
    if style not in SKETCH_STYLES:
        raise ApiError(422, f"Unknown sketch style '{style}'.", "invalid_style")
    fmt = validate_output_format(format)
    jpeg_quality = validate_quality(quality)
    style_options = parse_options(options)
    req_width = parse_int(width, "width")
    req_height = parse_int(height, "height")
    preserve = parse_bool(preserve_aspect_ratio, "preserve_aspect_ratio")

    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise ApiError(413, f"The maximum image size is {settings.max_upload_size_mb} MB.", "file_too_large")

    def work():
        started = time.perf_counter()
        image = decode_image(data, file.content_type, settings)
        out_w, out_h = resolve_output_dimensions(
            image.shape[1], image.shape[0], req_width, req_height, preserve, settings
        )
        sketch = generate_sketch(image, style, out_w, out_h, style_options)
        payload, media_type = encode_image(sketch, fmt, jpeg_quality)
        return payload, media_type, out_w, out_h, time.perf_counter() - started

    try:
        payload, media_type, out_w, out_h, elapsed = await _run_limited(request, work)
    except (ApiError, ProcessingError):
        raise
    except Exception:
        logger.exception("Unexpected sketch processing failure")
        raise ApiError(500, "An unexpected error occurred while processing the image.", "processing_error") from None

    extension = "png" if fmt == "png" else "jpg"
    filename = f"{sanitize_stem(file.filename)}_sketch.{extension}"
    return Response(
        content=payload,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Output-Width": str(out_w),
            "X-Output-Height": str(out_h),
            "X-Processing-Ms": str(int(elapsed * 1000)),
        },
    )

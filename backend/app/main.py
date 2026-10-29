import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router
from app.config import get_settings
from app.errors import ApiError
from app.services.sketch_service import ProcessingError

logger = logging.getLogger("sketchify")
settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Output-Width", "X-Output-Height", "X-Processing-Ms"],
)


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    # Reject obviously oversized bodies early; the route enforces the exact file limit.
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > settings.max_upload_bytes + 1024 * 1024:
        return error_response(413, "file_too_large", f"The maximum image size is {settings.max_upload_size_mb} MB.")
    return await call_next(request)


@app.exception_handler(ApiError)
async def handle_api_error(_: Request, exc: ApiError):
    return error_response(exc.status_code, exc.code, exc.message)


@app.exception_handler(ProcessingError)
async def handle_processing_error(_: Request, exc: ProcessingError):
    logger.error("Processing error: %s", exc)
    return error_response(500, "processing_error", "The sketch could not be generated.")


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError):
    fields = ", ".join(sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc")}))
    return error_response(400, "invalid_request", f"Missing or invalid request fields: {fields}.")


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(_: Request, exc: StarletteHTTPException):
    return error_response(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(Exception)
async def handle_unexpected(_: Request, exc: Exception):
    logger.exception("Unhandled error")
    return error_response(500, "internal_error", "An unexpected error occurred.")


app.include_router(router)

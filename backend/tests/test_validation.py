import io

import cv2
import numpy as np
import pytest
from PIL import Image

from app.config import get_settings
from app.errors import ApiError
from app.utils.validators import parse_options, resolve_output_dimensions, sanitize_stem

from .conftest import encode, post_sketch


def test_text_file_renamed_to_png_rejected(client):
    r = post_sketch(client, b"hello world, not an image", "fake.png", "image/png")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_image"


def test_pdf_renamed_to_jpg_rejected(client):
    r = post_sketch(client, b"%PDF-1.4\n%fake pdf content", "doc.jpg", "image/jpeg")
    assert r.status_code == 422


def test_webp_rejected(client, sample_bgr):
    buf = io.BytesIO()
    Image.fromarray(cv2.cvtColor(sample_bgr, cv2.COLOR_BGR2RGB)).save(buf, "WEBP")
    r = post_sketch(client, buf.getvalue(), "photo.webp", "image/webp")
    assert r.status_code == 415
    r = post_sketch(client, buf.getvalue(), "photo.jpg", "image/jpeg")
    assert r.status_code == 415


def test_empty_file_rejected(client):
    assert post_sketch(client, b"", "empty.png").status_code == 422


def test_corrupted_image_rejected(client, png_bytes):
    r = post_sketch(client, png_bytes[: len(png_bytes) // 2], "broken.png")
    assert r.status_code == 422


def test_mime_inconsistent_with_contents(client, png_bytes):
    r = post_sketch(client, png_bytes, "photo.jpg", "image/jpeg")
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "type_mismatch"


def test_bad_extension_and_mime(client, png_bytes):
    assert post_sketch(client, png_bytes, "photo.gif", "image/png").status_code == 415
    assert post_sketch(client, png_bytes, "photo.png", "image/gif").status_code == 415


def test_oversized_upload(client):
    big = b"\x89PNG" + b"0" * (10 * 1024 * 1024 + 10)
    assert post_sketch(client, big).status_code == 413


def test_image_too_small(client):
    tiny = np.zeros((16, 16, 3), np.uint8)
    assert post_sketch(client, encode(tiny), width="16", height="16").status_code == 422


def test_image_too_large_dimensions(client):
    wide = np.zeros((40, 8100, 3), np.uint8)
    assert post_sketch(client, encode(wide), width="100", height="100").status_code == 422


def test_pixel_limit(client):
    big = np.zeros((5100, 5100, 3), np.uint8)  # 26 MP, compresses to almost nothing
    r = post_sketch(client, encode(big), width="100", height="100")
    assert r.status_code == 422


def test_animated_png_rejected(client, sample_bgr):
    rgb = Image.fromarray(cv2.cvtColor(sample_bgr, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    rgb.save(buf, "PNG", save_all=True, append_images=[rgb.transpose(Image.FLIP_LEFT_RIGHT)], duration=100)
    assert post_sketch(client, buf.getvalue()).status_code == 422


def test_transparent_png_composited_on_white(client):
    rgba = np.zeros((64, 64, 4), np.uint8)  # fully transparent
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG")
    r = post_sketch(client, buf.getvalue(), width="64", height="64")
    assert r.status_code == 200
    out = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_GRAYSCALE)
    assert out.mean() > 240  # blank white page, not black


def test_options_validation():
    assert parse_options(None) == {}
    assert parse_options('{"intensity": 80}')["intensity"] == 80
    for bad in ('{"intensity": 150}', '{"nope": 1}', '{"intensity": "x"}', '{"intensity": true}'):
        with pytest.raises(ApiError) as exc:
            parse_options(bad)
        assert exc.value.status_code == 422
    for bad in ("not json", "[1,2]"):
        with pytest.raises(ApiError) as exc:
            parse_options(bad)
        assert exc.value.status_code == 400


def test_resolve_dimensions_preserves_ratio():
    s = get_settings()
    assert resolve_output_dimensions(1920, 1080, 1280, 999, True, s) == (1280, 720)
    assert resolve_output_dimensions(1920, 1080, 1280, 999, False, s) == (1280, 999)
    with pytest.raises(ApiError):
        resolve_output_dimensions(100, 100, 9000, 100, False, s)
    with pytest.raises(ApiError):
        resolve_output_dimensions(100, 100, 7000, 7000, False, s)  # exceeds pixel cap
    with pytest.raises(ApiError):
        resolve_output_dimensions(100, 100, 0, 10, False, s)


def test_sanitize_stem():
    assert sanitize_stem("../../my photo (1).jpg") == "my_photo_1"
    assert sanitize_stem("") == "image"
    assert sanitize_stem("***.png") == "image"

import cv2
import numpy as np
import pytest

from app.services.styles import SKETCH_STYLES
from app.services import sketch_service

from .conftest import post_sketch


def decode(content):
    return cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_UNCHANGED)


@pytest.mark.parametrize("style", list(SKETCH_STYLES))
def test_every_style_png(client, png_bytes, style):
    r = post_sketch(client, png_bytes, style=style)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert decode(r.content).shape[:2] == (240, 320)


@pytest.mark.parametrize("style", list(SKETCH_STYLES))
def test_every_style_jpg(client, jpg_bytes, style):
    r = post_sketch(client, jpg_bytes, "photo.jpg", "image/jpeg", style=style, format="jpg")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content[:3] == b"\xff\xd8\xff"
    assert 'filename="photo_sketch.jpg"' in r.headers["content-disposition"]


def test_png_response_headers(client, png_bytes):
    r = post_sketch(client, png_bytes)
    assert r.headers["x-output-width"] == "320"
    assert r.headers["x-output-height"] == "240"
    assert 'filename="photo_sketch.png"' in r.headers["content-disposition"]


def test_aspect_ratio_preserved_adjusts_height(client, png_bytes):
    r = post_sketch(client, png_bytes, width="160", height="999", preserve_aspect_ratio="true")
    assert r.status_code == 200
    assert (r.headers["x-output-width"], r.headers["x-output-height"]) == ("160", "120")
    assert decode(r.content).shape[:2] == (120, 160)


def test_aspect_ratio_not_preserved(client, png_bytes):
    r = post_sketch(client, png_bytes, width="200", height="200", preserve_aspect_ratio="false")
    assert decode(r.content).shape[:2] == (200, 200)


def test_jpeg_quality_affects_size(client, png_bytes):
    low = post_sketch(client, png_bytes, style="crosshatch", format="jpg", quality="10")
    high = post_sketch(client, png_bytes, style="crosshatch", format="jpg", quality="100")
    assert len(low.content) < len(high.content)


def test_png_ignores_quality(client, png_bytes):
    a = post_sketch(client, png_bytes, quality="10")
    b = post_sketch(client, png_bytes, quality="100")
    assert a.content == b.content


def test_options_applied(client, png_bytes):
    a = post_sketch(client, png_bytes, style="ink_outline", options='{"line_thickness": 0}')
    b = post_sketch(client, png_bytes, style="ink_outline", options='{"line_thickness": 100}')
    assert a.status_code == b.status_code == 200
    assert a.content != b.content


@pytest.mark.parametrize(
    "overrides,status",
    [
        ({"style": "watercolor"}, 422),
        ({"format": "gif"}, 422),
        ({"quality": "5"}, 422),
        ({"quality": "101"}, 422),
        ({"quality": "abc"}, 400),
        ({"width": "0"}, 422),
        ({"width": "-5", "preserve_aspect_ratio": "false"}, 422),
        ({"width": "abc"}, 400),
        ({"width": "9000"}, 422),
        ({"preserve_aspect_ratio": "maybe"}, 400),
        ({"options": '{"intensity": 500}'}, 422),
        ({"options": "{bad"}, 400),
    ],
)
def test_invalid_parameters(client, png_bytes, overrides, status):
    r = post_sketch(client, png_bytes, **overrides)
    assert r.status_code == status
    assert "message" in r.json()["error"]


def test_missing_fields(client, png_bytes):
    r = client.post("/api/sketch", files={"file": ("a.png", png_bytes, "image/png")})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_request"


def test_processing_failure_returns_structured_500(client, png_bytes, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    monkeypatch.setitem(SKETCH_STYLES, "classic_pencil", boom)
    r = post_sketch(client, png_bytes)
    assert r.status_code == 500
    assert "secret" not in r.text
    assert "error" in r.json()


def test_bad_style_output_returns_500(client, png_bytes, monkeypatch):
    monkeypatch.setitem(SKETCH_STYLES, "classic_pencil", lambda *a, **k: np.zeros((3, 3), np.uint8))
    assert post_sketch(client, png_bytes).status_code == 500


def test_cors_headers(client):
    r = client.options(
        "/api/sketch",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_encode_rejects_unknown_format():
    with pytest.raises(Exception):
        sketch_service.encode_image(np.zeros((4, 4), np.uint8), "bmp", 90)

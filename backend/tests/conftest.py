import io
import os
import sys

import cv2
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app  # noqa: E402
from app.utils.sample import make_sample_image  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def sample_bgr():
    return make_sample_image(320, 240)


def encode(image, ext=".png", quality=90):
    params = [cv2.IMWRITE_JPEG_QUALITY, quality] if ext == ".jpg" else []
    ok, buf = cv2.imencode(ext, image, params)
    assert ok
    return buf.tobytes()


@pytest.fixture()
def png_bytes(sample_bgr):
    return encode(sample_bgr, ".png")


@pytest.fixture()
def jpg_bytes(sample_bgr):
    return encode(sample_bgr, ".jpg")


def post_sketch(client, data, filename="photo.png", mime="image/png", **overrides):
    fields = {
        "style": "classic_pencil",
        "width": "320",
        "height": "240",
        "preserve_aspect_ratio": "true",
        "format": "png",
        "quality": "90",
    }
    fields.update({k: v for k, v in overrides.items() if v is not None})
    return client.post("/api/sketch", files={"file": (filename, io.BytesIO(data), mime)}, data=fields)

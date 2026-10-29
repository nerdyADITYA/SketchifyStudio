import numpy as np
import pytest

from app.services.sketch_service import generate_sketch
from app.services.styles import SKETCH_STYLES
from app.utils.sample import make_sample_image
from app.utils.validators import parse_options

from .conftest import post_sketch


@pytest.mark.parametrize("name", list(SKETCH_STYLES))
def test_color_mode_returns_three_channels(name):
    img = make_sample_image(200, 150)
    out = generate_sketch(img, name, 200, 150, {"color_mode": "color"})
    assert out.shape == (150, 200, 3)
    channels = out.astype(int)
    assert np.abs(channels[..., 0] - channels[..., 2]).mean() > 2  # genuinely coloured


def test_color_strength_zero_is_nearly_gray():
    img = make_sample_image(200, 150)
    out = generate_sketch(img, "classic_pencil", 200, 150, {"color_mode": "color", "color_strength": 0})
    assert np.abs(out[..., 0].astype(int) - out[..., 2].astype(int)).max() <= 1


def test_option_validation():
    assert parse_options('{"color_mode": "color"}')["color_mode"] == "color"
    assert parse_options(None) == {}
    for bad in ('{"color_mode": "sepia"}', '{"color_strength": 101}'):
        with pytest.raises(Exception):
            parse_options(bad)


def test_api_color_output(client, png_bytes):
    r = post_sketch(client, png_bytes, style="cartoon_sketch", options='{"color_mode": "color"}')
    assert r.status_code == 200

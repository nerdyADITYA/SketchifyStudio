import itertools

import numpy as np
import pytest

from app.services.sketch_service import generate_sketch
from app.services.styles import SKETCH_STYLES
from app.utils.sample import make_sample_image


@pytest.fixture(scope="module")
def results():
    img = make_sample_image(400, 300)
    return {name: generate_sketch(img, name, 400, 300, {}) for name in SKETCH_STYLES}


def test_eight_styles_registered():
    assert len(SKETCH_STYLES) == 8


@pytest.mark.parametrize("name", list(SKETCH_STYLES))
def test_style_output_valid(results, name):
    out = results[name]
    assert out.dtype == np.uint8
    assert out.shape[:2] == (300, 400)
    assert out.std() > 5  # not blank
    assert out.mean() > 100  # mostly paper-coloured, not black


def test_styles_are_visually_distinct(results):
    for a, b in itertools.combinations(results, 2):
        diff = np.abs(results[a].astype(int) - results[b].astype(int)).mean()
        assert diff > 1.0,f"{a} and {b} look too similar ({diff:.2f})"


@pytest.mark.parametrize("name", list(SKETCH_STYLES))
def test_style_resizes_and_handles_edge_cases(name):
    gen = SKETCH_STYLES[name]
    img = make_sample_image(200, 150)
    assert gen(img, 100, 75, {}).shape == (75, 100)  # downscale
    assert gen(img, 300, 225, {}).shape == (225, 300)  # upscale
    flat = np.full((64, 64, 3), 128, np.uint8)  # featureless
    assert gen(flat, 64, 64, {}).shape == (64, 64)
    black = np.zeros((64, 64, 3), np.uint8)
    assert gen(black, 64, 64, {}).shape == (64, 64)
    white = np.full((64, 64, 3), 255, np.uint8)
    assert gen(white, 64, 64, {}).shape == (64, 64)


@pytest.mark.parametrize("name", list(SKETCH_STYLES))
def test_options_change_output_and_extremes_work(name):
    gen = SKETCH_STYLES[name]
    img = make_sample_image(240, 180)
    for key in ("intensity", "line_thickness", "contrast", "detail", "shading"):
        for value in (0, 100):
            assert gen(img, 240, 180, {key: value}).shape == (180, 240)
    low = gen(img, 240, 180, {"intensity": 0})
    high = gen(img, 240, 180, {"intensity": 100})
    assert not np.array_equal(low, high)


def test_invalid_input_rejected():
    with pytest.raises(ValueError):
        SKETCH_STYLES["classic_pencil"](None, 10, 10)


@pytest.mark.parametrize("name", ["ink_outline", "line_art", "fine_pencil"])
@pytest.mark.parametrize("size", [(300, 500), (900, 1600)])
def test_edge_styles_not_blank_on_dark_photo(name, size):
    dark = (make_sample_image(300, 500).astype(np.float32) * 0.2).astype(np.uint8)
    out = SKETCH_STYLES[name](dark, *size, {})
    assert (out < 128).mean() > 0.0005, "dark photo produced a blank sketch"

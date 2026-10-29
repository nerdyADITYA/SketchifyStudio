import numpy as np

from ._common import adjust_contrast, dodge, finish, level, prepare_gray, scale_for


def generate(image, width, height, options=None):
    """Soft pencil drawing: grayscale -> invert -> blur -> colour dodge."""
    gray = prepare_gray(image, width, height)
    s = scale_for(width, height)

    shading = level(options, "shading")
    intensity = level(options, "intensity")
    contrast = level(options, "contrast")

    sketch = dodge(gray, sigma=6.0 * s * (0.5 + shading)).astype(np.float32)
    sketch = 255.0 - (255.0 - sketch) * (0.5 + intensity)
    sketch = adjust_contrast(sketch, 0.6 + 0.8 * contrast, pivot=200.0)
    return finish(sketch)

"""Procedural sample scene used for style thumbnails and tests (no external assets needed)."""
import cv2
import numpy as np


def make_sample_image(width: int = 640, height: int = 480) -> np.ndarray:
    """Return a BGR landscape with a sky gradient, sun, hills, a house and trees."""
    rng = np.random.default_rng(42)
    s = height / 480.0
    img = np.zeros((height, width, 3), np.uint8)

    # Sky gradient
    t = np.linspace(0, 1, height, dtype=np.float32)[:, None]
    top = np.array([200, 140, 70], np.float32)
    bottom = np.array([250, 225, 190], np.float32)
    img[:] = (top * (1 - t) + bottom * t)[:, None, :].astype(np.uint8)

    def P(x, y):
        return int(x * width), int(y * height)

    cv2.circle(img, P(0.78, 0.2), int(45 * s), (120, 220, 250), -1, cv2.LINE_AA)

    # Hills
    xs = np.arange(width)
    far = (0.62 + 0.06 * np.sin(xs / width * 5.0)) * height
    near = (0.78 + 0.05 * np.sin(xs / width * 7.0 + 1.5)) * height
    for x in xs:
        img[int(far[x]):, x] = (90, 130, 80)
        img[int(near[x]):, x] = (50, 150, 70)

    # House
    x0, y0 = P(0.22, 0.52)
    x1, y1 = P(0.52, 0.80)
    cv2.rectangle(img, (x0, y0), (x1, y1), (150, 190, 225), -1)
    roof = np.array([[x0 - int(15 * s), y0], [x1 + int(15 * s), y0], [(x0 + x1) // 2, y0 - int(80 * s)]])
    cv2.fillPoly(img, [roof], (40, 60, 150))
    cv2.rectangle(img, P(0.30, 0.64), P(0.36, 0.80), (30, 50, 80), -1)
    cv2.rectangle(img, P(0.41, 0.58), P(0.47, 0.66), (240, 220, 140), -1)
    cv2.rectangle(img, P(0.41, 0.58), P(0.47, 0.66), (40, 40, 40), max(1, int(2 * s)))

    # Trees
    for cx, cy, r in ((0.68, 0.62, 0.09), (0.84, 0.66, 0.07), (0.08, 0.66, 0.07)):
        cv2.rectangle(img, P(cx - 0.012, cy), P(cx + 0.012, cy + 0.15), (30, 60, 100), -1)
        cv2.circle(img, P(cx, cy), int(r * height), (40, 110, 40), -1, cv2.LINE_AA)
        cv2.circle(img, P(cx - 0.02, cy - 0.02), int(r * height * 0.6), (60, 150, 60), -1, cv2.LINE_AA)

    img = cv2.GaussianBlur(img, (0, 0), 0.8).astype(np.float32)

    # Photo-like touches: soft lighting, a vignette, surface texture and sensor noise.
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    light = 1.1 - 0.35 * (xx / width) - 0.1 * (yy / height)
    vignette = 1.0 - 0.35 * (((xx / width - 0.5) ** 2 + (yy / height - 0.5) ** 2) * 2)
    texture = cv2.GaussianBlur(rng.normal(0, 1, (height, width)).astype(np.float32), (0, 0), 1.5 * s) * 9
    grain = rng.normal(0, 4, img.shape).astype(np.float32)
    img = img * (light * vignette)[..., None] + texture[..., None] + grain
    return np.clip(img, 0, 255).astype(np.uint8)

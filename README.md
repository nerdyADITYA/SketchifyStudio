# Sketchify Studio

**A full-stack computer vision project that turns photographs into sketches.**

Upload a photo, pick one of eight sketch styles, choose black-and-white or colour, set the output size and format, and download the result. All image processing is done with classical computer vision (OpenCV and NumPy). There is no AI model, no login, no database, and no image is ever saved on the server.

> This README is the single source of truth for the project. If something here disagrees with another note, this file wins.

---

## Table of contents

1. [What the project does](#1-what-the-project-does)
2. [How it works (big picture)](#2-how-it-works-big-picture)
3. [Technology used](#3-technology-used)
4. [Computer vision basics you need first](#4-computer-vision-basics-you-need-first)
5. [The eight sketch styles (the algorithms)](#5-the-eight-sketch-styles-the-algorithms)
6. [Black and white versus colour](#6-black-and-white-versus-colour)
7. [The customisation sliders](#7-the-customisation-sliders)
8. [Rules and validation](#8-rules-and-validation)
9. [The API](#9-the-api)
10. [The website (frontend)](#10-the-website-frontend)
11. [Project folder map](#11-project-folder-map)
12. [How to run it](#12-how-to-run-it)
13. [Testing](#13-testing)
14. [Problems we hit and how we fixed them](#14-problems-we-hit-and-how-we-fixed-them)
15. [Limitations and future ideas](#15-limitations-and-future-ideas)
16. [Glossary](#16-glossary)

---

## 1. What the project does

| You do this | The app does this |
|---|---|
| Drag a JPG or PNG onto the page | Checks it is a real, safe image and shows its size, format and dimensions |
| Pick a sketch style | Shows eight cards, each with a thumbnail made by our own algorithms |
| Pick **Black & white** or **Original colours** | Produces a grey pencil-style drawing or a coloured drawing |
| Move the fine-tune sliders (optional) | Changes intensity, line thickness, contrast, detail, shading |
| Choose width, height, PNG or JPG, quality | Resizes the picture before sketching and encodes the result |
| Press **Generate Sketch** | Sends the photo to the Python server, which draws the sketch and sends it back |
| Press **Download Sketch** | Saves a file such as `portrait_sketch.png` |

The eight styles: **Classic Pencil, Fine Pencil, Dark Pencil, Charcoal, Ink Outline, Line Art, Crosshatch, Cartoon Sketch.**

Out of scope on purpose: user accounts, a database, saved history, payments, and cloud AI image generation.

---

## 2. How it works (big picture)

```
 Browser (React)                          Server (FastAPI + OpenCV)
 ───────────────                          ─────────────────────────
 1. User picks a photo
 2. Frontend checks it (type, size,
    can the browser open it?)
 3. User picks style + settings
 4. POST /api/sketch  ─────────────────►  5. Re-check everything (never trust the browser)
    (photo + settings as a form)          6. Decode photo → resize to requested size
                                          7. Run the chosen style's algorithm
                                          8. Optional: add colour
                                          9. Encode as PNG or JPG
 11. Show preview, allow download  ◄────  10. Send the image back (plus its size in headers)
```

Key design ideas:

- **Two layers of checking.** The browser checks files to give instant, friendly errors. The server checks again, because a browser check can be bypassed.
- **Everything happens in memory.** The photo is never written to disk.
- **One shared interface.** Every style is a Python function with the same signature, `generate(image, width, height, options)`, so adding a ninth style is easy.
- **One shared encoder.** PNG and JPG export works the same for every style.

---

## 3. Technology used

| Part | Tool | Why |
|---|---|---|
| Website | React + Vite (plain JavaScript/JSX, no TypeScript) | Fast, component-based interface |
| Web requests | Axios | Sends the photo and receives the image |
| Icons | Lucide React | Upload/download icons |
| Server | Python 3.11+ and FastAPI (run by Uvicorn) | Simple, fast REST API |
| Image processing | OpenCV (`opencv-python-headless`) and NumPy | All sketch algorithms |
| Image safety checks | Pillow | Reads the real file contents, metadata, transparency, rotation |
| Settings | pydantic-settings | Loads limits from environment variables |
| Tests | pytest + httpx | 100 automated backend tests |

---

## 4. Computer vision basics you need first

A digital image is a grid of pixels. A grey image has one number per pixel (0 = black, 255 = white). A colour image has three numbers per pixel (blue, green, red in OpenCV).

These building blocks are reused by many styles.

### 4.1 Grayscale
Converts colour to a single brightness value per pixel. Every style starts here.

### 4.2 Gaussian blur
Replaces each pixel with a weighted average of its neighbours. Smooths the picture and hides noise. The **sigma** value controls how strong the blur is.

### 4.3 Bilateral filter
A blur that **keeps edges sharp**. It only averages pixels that are close in position *and* similar in brightness. Used to flatten textures (skin, grass) without smearing outlines.

### 4.4 Colour dodge (the classic pencil trick)
1. Invert the grey image (`255 − pixel`).
2. Blur the inverted image.
3. Invert the blur again.
4. Divide the original grey image by that result (`grey ÷ inverted_blur × 256`).

Flat areas become white paper. Areas where brightness changes quickly (edges, texture) stay dark, which looks like pencil strokes.

### 4.5 Edge detection (Canny)
Finds the outlines of objects by looking for sudden brightness changes (the gradient, measured with the **Sobel** operator). Canny uses two thresholds: a *high* one to start an edge and a *low* one to let it continue. Result: thin 1-pixel lines.

**Our smart threshold (`auto_canny`).** A common recipe sets thresholds from the picture's average brightness, but that failed on bright and dark photos (a night photo produced a **blank** Line Art result). Ours works like this:
1. Stretch the brightness range using the 1st and 99th percentiles, so dark or flat photos get usable contrast.
2. Measure the Sobel gradient strength of every pixel.
3. Set the high threshold to the 92nd percentile of that strength (times a `scale` factor), limited to 90–500.
4. Set the low threshold to 40% of the high one.

A lower `scale` keeps more edges (more detail).

### 4.6 Morphology
Shape operations on black-and-white masks:
- **Dilate** makes lines thicker.
- **Close** joins small gaps in lines.

### 4.7 Adaptive threshold
Turns a grey image into pure black/white by comparing each pixel with the average of its **local neighbourhood**, so it works even when lighting is uneven.

### 4.8 CLAHE
Local contrast boosting. It brings out detail in dark and light areas separately.

### 4.9 Posterising (quantising)
Reduces the number of tones, for example from 256 levels to 6. Gives flat "poster" regions.

### 4.10 Connected components
Groups touching line pixels into separate pieces so we can measure each piece and delete tiny specks.

### 4.11 The "scale factor" `s`
A 4000 px photo needs thicker strokes and bigger blur than a 400 px one, or the style would look different at different sizes. We compute

```
s = sqrt(width × height) / 1000      (limited to 0.35 – 4.0)
```

and multiply blur sizes, line widths, and spacing by `s`. A 1000×1000 image has `s = 1`.

### 4.12 Resizing
The photo is resized to the requested output size **before** sketching. We use `INTER_AREA` when shrinking (best quality) and `INTER_CUBIC` when enlarging.

---

## 5. The eight sketch styles (the algorithms)

Each style lives in its own file in `backend/app/services/styles/`. Every style returns a **grey image** (one channel) with a white paper background, except Cartoon Sketch in colour mode (see section 6).

In the formulas below, the sliders are written as numbers between 0 and 1 (the slider value ÷ 100, default 0.5): `intensity`, `shading`, `contrast`, `detail`, `thickness`. "Contrast f, pivot p" means `(pixel − p) × f + p`.

### 5.1 Classic Pencil — `classic_pencil.py`
*Soft shading, like a traditional pencil drawing.*

1. Convert to grey.
2. Colour dodge (section 4.4) with blur sigma = `6 × s × (0.5 + shading)`.
3. Intensity: `255 − (255 − sketch) × (0.5 + intensity)`; stronger intensity makes darker strokes.
4. Contrast with `f = 0.6 + 0.8 × contrast`, pivot 200.

**Look:** light, soft, grainy shading. Flat areas stay white.

### 5.2 Fine Pencil — `fine_pencil.py`
*Delicate thin lines with very light shading.*

1. Convert to grey, reduce noise (bilateral filter + light Gaussian blur).
2. Detect thin edges with `auto_canny` (`scale = 1.4 − 0.8 × detail`), slightly softened.
3. Make a very faint shading layer: dodge with sigma `10 × s`, then lighten it heavily (`255 − (255 − shade) × (0.15 + 0.4 × shading)`).
4. Darken the shading wherever there is an edge: `shade × (1 − edge × (0.5 + 0.7 × intensity))` (edge darkening capped at 92%).
5. Contrast with `f = 0.8 + 0.5 × contrast`, pivot 220.

**Look:** fine outlines that keep small details, without heavy darkness.

### 5.3 Dark Pencil — `dark_pencil.py`
*Bold pencil with strong contrast and dramatic shadows.*

1. Dodge pencil with a smaller blur (sigma `4 × s × (0.5 + shading)`) for tighter shading.
2. **Gamma darkening:** `255 × (pixel/255) ^ (1 + 1.6 × intensity)`. White stays white (highlights are protected) but mid-tones get much darker.
3. Add **stroke darkening** from the Sobel gradient strength (normalised by its 99th percentile): subtract `140 × (0.4 + 0.8 × detail) × strength`.
4. Contrast with `f = 1 + 0.6 × contrast`, pivot 150.

**Look:** thick, dark outlines and deep shading, good for portraits and dramatic photos.

### 5.4 Charcoal — `charcoal.py`
*Broad, smudgy, dramatic tones with a paper texture.*

1. Grey → **CLAHE** (clip limit `1.5 + 4 × contrast`) → bilateral filter → Gaussian blur.
2. Convert to darkness (`1 − brightness`) and **posterise** to `4 + round(4 × detail)` tone levels, then blur the steps so they blend.
3. Build "masses": an **adaptive threshold** (local black/white regions) that is blurred.
4. Mix: `tone = 0.65 × posterised + 0.35 × masses`.
5. Re-map so light areas become bare paper: `(tone − 0.2) / 0.8`.
6. Shadow depth: raise to the power `1.3 − 0.6 × shading` (a lower power makes shadows darker).
7. Add **paper grain**: blurred random noise (fixed seed, so results are repeatable), applied mostly in dark areas.
8. Scale by `0.6 + 0.9 × intensity` and output `250 − 250 × tone` (a very slightly off-white paper).

**Look:** big soft dark shapes, grainy texture, strong shadows.

### 5.5 Ink Outline — `ink_outline.py`
*Clean black outlines on white, like a pen-and-ink drawing.*

1. Grey → Gaussian blur (sigma `1.0 × s + 0.5`).
2. `auto_canny` edges (`scale = 1.5 − 0.8 × detail`).
3. **Dilate** the edges to thickness `round((1 + 4 × thickness) × s)` pixels.
4. **Close** small gaps (3×3), then lightly blur so lines look smooth (anti-aliasing).
5. Ink strength `0.6 + 0.8 × intensity`, then invert so lines are black on white, contrast `f = 0.7 + 0.6 × contrast`.

**Look:** bold outlines, almost no shading. Good for buildings and objects.

### 5.6 Line Art — `line_art.py`
*Minimal, tidy outlines, like a colouring-book page.*

1. Heavy smoothing: median blur → bilateral filter → Gaussian blur (sigma `1.5 × s`). This removes textures so only important shapes remain.
2. `auto_canny` (`scale = 1.8 − 1.0 × detail`, i.e. a stricter detector than Ink Outline).
3. **Remove small fragments** using connected components: any piece with fewer than `(15 + 60 × (1 − detail)) × s` pixels is deleted. (A thin line's pixel count grows with its *length*, so the cut-off uses `s`, not `s²`.)
4. **Close** gaps (5×5) to join broken lines.
5. Thicken to `round((1 + 2 × thickness) × s)` px, anti-alias, and invert to black-on-white.

**Look:** fewer, cleaner, thinner lines than Ink Outline.

### 5.7 Crosshatch — `crosshatch.py`
*Hand-drawn shading made of crossing lines; darker areas get more layers.*

1. Blur the grey image (sigma `1.5 × s`) and apply contrast.
2. Make four **layers of parallel lines**. Each layer is switched on only where the picture is darker than its threshold:

| Layer | Brightness threshold | Line angle |
|---|---|---|
| 1 | below 185 | 45° |
| 2 | below 140 | 135° |
| 3 | below 95 | 0° (horizontal) |
| 4 | below 55 | 90° (vertical) |

   Light areas get no or one set of lines; the darkest areas get all four crossing each other.
3. Line spacing is `max(3, (8 − 3.5 × shading) × s)`; line width is `spacing × (0.18 + 0.25 × thickness)`. A small sine wobble makes the lines look hand-drawn instead of ruler-straight.
4. `intensity` shifts all thresholds by `(intensity − 0.5) × 70` (more intensity = more hatching).
5. Overlay the Canny outlines (`scale = 1.6 − 0.9 × detail`) using the darker of hatch and outline at each pixel.

**Look:** directional pen strokes with real tonal shading.

### 5.8 Cartoon Sketch — `cartoon_sketch.py`
*Flat simplified tones with thick dark outlines.*

1. **Smooth** with three passes of the bilateral filter (on a copy capped at 1600 px for speed, then scaled back up). Textures vanish but edges stay.
2. **Posterise** into `3 + round(6 × detail)` flat tone bands, taking the middle of each band, then lighten with gamma 0.6 so the paper stays bright.
3. **Outlines:** median blur → *adaptive mean threshold* (block size about `11 × s`) finds local dark lines. They are thickened to `round((1 + 2.5 × thickness) × s)` px, softened, and strength-scaled by `0.6 + 0.8 × intensity` (capped at 95% black).
4. Multiply tones × outlines, then apply contrast.

**Look:** comic/illustration style. In colour mode it keeps the photo's colours (section 6.2).

### Style comparison

| Style | Core technique | Lines | Shading | Best for |
|---|---|---|---|---|
| Classic Pencil | Colour dodge | Soft | Soft | General photos |
| Fine Pencil | Canny + faint dodge | Thin | Very light | Portraits, details |
| Dark Pencil | Dodge + gamma + Sobel strokes | Bold | Strong | Dramatic photos |
| Charcoal | CLAHE + posterise + adaptive mass + grain | None | Broad, deep | Artistic portraits |
| Ink Outline | Canny + dilate | Bold | None | Buildings, objects |
| Line Art | Heavy smoothing + Canny + speck removal | Thin, clean | None | Illustration |
| Crosshatch | Angled line layers by brightness + Canny | Hatch | Line density | Pen-and-ink look |
| Cartoon Sketch | Bilateral + posterise + adaptive outlines | Thick | Flat bands | Stylised art |

---

## 6. Black and white versus colour

The **colour** control appears under "Fine-tune" for every style. The default is **Black & white**.

### 6.1 How black and white works
Every style converts the photo to a single grey channel at the start (`cv2.cvtColor(..., COLOR_BGR2GRAY)`) and draws entirely in grey values: 0 (ink) to 255 (white paper). The result is a one-channel image, so PNG files are small and the style looks like a real pencil/ink drawing. **Black & white is exactly what you get when colour is off.**

### 6.2 How colour works
There are two ways, chosen automatically:

**A. Tinting (all styles except Cartoon Sketch) — `colorize()` in `_common.py`**

The grey sketch is drawn first. Then we multiply it by a colour layer made from the original photo:

1. Resize the original photo to the output size (and lightly smooth it with a bilateral filter if the image is 4 MP or smaller).
2. Convert to HSV. **Boost saturation ×1.25** and **lighten** brightness with `V^0.55` so colours are not too dark.
3. `tint = 1 − strength × (1 − photo_colour)` — at strength 0 the tint is pure white (no colour); at 100% it is the full lightened photo colour.
4. **Multiply:** `colour_sketch = grey_sketch × tint`.

Because it is a multiplication, black lines stay black (0 × anything = 0), and white paper takes on the photo's colour. Result: a coloured pencil / ink drawing where the shading and lines are exactly the same as the black-and-white version.

**B. Native colour (Cartoon Sketch only)**

Cartoon colour is built from the photo itself rather than tinting a grey drawing:

1. Smooth the **colour** image with three bilateral-filter passes.
2. Posterise **each colour channel** into `bands + 3` levels (extra levels keep hues recognisable).
3. Boost saturation ×1.2.
4. `strength` blends toward the grey version of the same picture: `grey + (colour − grey) × strength`.
5. Multiply by the same outline mask used in black and white, then apply contrast.

Smooth gradients (like a night sky) show visible colour bands. That is normal posterising; a higher **Detail** slider means more bands.

### 6.3 Colour strength
`color_strength` (0–100, default 100) controls how much of the photo's colour shows. At 0 the result is grey again.

### 6.4 What the colour image looks like in the file
Colour results have three channels, so they are larger files than black and white. Both encode as PNG (lossless) or JPG.

---

## 7. The customisation sliders

All sliders go from 0 to 100 and start at 50. Only the sliders that make sense for a style are shown.

| Slider | Meaning | Used by |
|---|---|---|
| Sketch intensity | Overall strength of the effect | All eight |
| Line thickness | Width of lines and strokes | Ink Outline, Line Art, Crosshatch, Cartoon |
| Contrast | Gap between dark and light | Everything except Line Art |
| Detail level | How much fine detail is kept | Fine Pencil, Dark Pencil, Charcoal, Ink Outline, Line Art, Crosshatch, Cartoon |
| Shading strength | Depth of tonal shading | Classic, Fine, Dark, Charcoal, Crosshatch |
| Colour | `grayscale` or `color` | All eight |
| Colour strength | 0–100 (default 100) | Shown when Colour is on |

The server validates every value. Unknown option names, text where a number is expected, or numbers outside 0–100 are rejected with a clear message. Only options the user changed are sent.

---

## 8. Rules and validation

| Rule | Value |
|---|---|
| Allowed input types | JPG, JPEG, PNG |
| Maximum upload size | 10 MB |
| Input dimensions | 32 to 8000 px per side |
| Input total pixels | at most 25 megapixels |
| Output dimensions | 16 to 8000 px per side, at most 25 megapixels |
| JPEG quality | 10 to 100 (default 90). PNG is lossless; the slider is disabled for PNG |
| Output formats | PNG or JPG |

All limits are configurable in `backend/.env`.

**Checks the server performs on every upload:**
file extension; declared MIME type; the *real* format found by decoding the file (a renamed PDF or WebP is rejected); that the declared type matches the real type; empty, corrupt, or truncated files; animated/multi-frame images; image size limits (checked **before** pixel data is decoded, which protects against "decompression bomb" files); then style, dimensions, format, quality, and options.

**Image handling details:**
- Transparent PNGs are placed on a **white** background so transparency never turns into black.
- Photos that carry a rotation flag (EXIF) are rotated correctly, matching what browsers show.
- 16-bit and other colour modes are converted to normal 8-bit RGB.
- Filenames from users are never used for disk paths; downloaded names are cleaned (`My Photo (1).jpg` → `My_Photo_1_sketch.png`).

**Protection against overload:** at most 2 sketches run at once; a request waits up to 5 seconds for a free slot (otherwise a "busy" error); processing stops waiting after 90 seconds.

**Aspect ratio:** when "Preserve aspect ratio" is on, `height = round(width ÷ original_width × original_height)`, and the server returns the real final size in headers.

---

## 9. The API

Base URL for local development: `http://localhost:8000`

### `GET /api/health`
Returns `{"status": "ok", "service": "sketchify-studio-api"}`.

### `POST /api/sketch` (multipart form data)

| Field | Required | Description |
|---|---|---|
| `file` | yes | The JPG/PNG photo |
| `style` | yes | `classic_pencil`, `fine_pencil`, `dark_pencil`, `charcoal`, `ink_outline`, `line_art`, `crosshatch`, `cartoon_sketch` |
| `width`, `height` | yes | Requested output size |
| `format` | yes | `png` or `jpg` |
| `preserve_aspect_ratio` | no | `true` (default) or `false` |
| `quality` | no | 10–100 for JPG |
| `options` | no | JSON text, e.g. `{"intensity": 70, "color_mode": "color", "color_strength": 80}` |

**Success:** the image bytes with the correct `Content-Type` (`image/png` or `image/jpeg`), plus headers `X-Output-Width`, `X-Output-Height`, `X-Processing-Ms`, and `Content-Disposition` with the filename.

**Errors** are always JSON: `{"error": {"code": "...", "message": "..."}}`

| Status | Meaning |
|---|---|
| 400 | Missing or malformed field (e.g. width not a number, bad JSON) |
| 413 | File too large |
| 415 | Unsupported file type or type does not match contents |
| 422 | Invalid image, dimensions, style, quality or option values |
| 500 | Unexpected processing failure (details hidden from the user) |
| 503 | Server busy |
| 504 | Processing timed out |

---

## 10. The website (frontend)

**Flow:** Upload → Choose style → Fine-tune → Output settings → Generate → Preview → Download.

**Layout:** before an image is chosen, a centred upload box. After upload, a two-column workspace: the **original and result previews on the left** (they stay in view while you scroll) and the **style cards, fine-tune controls and output settings on the right**. On narrow screens everything stacks in one column.

**Components** (`frontend/src/components/`):

| File | Job |
|---|---|
| `Header.jsx`, `Footer.jsx` | Page header and footer |
| `UploadZone.jsx` | Drag-and-drop or browse; keyboard accessible |
| `ImageInfo.jsx` | Filename, format, dimensions, size, chosen output |
| `ImagePreview.jsx` | Shows an image |
| `SketchStyleSelector.jsx` | The eight style cards (arrow-key navigation) |
| `StyleControls.jsx` | Sliders and the colour toggle |
| `OutputSettings.jsx` | Width, height, aspect ratio, format, quality |
| `ProcessingStatus.jsx` | Spinner and Cancel button |
| `SketchResult.jsx` | Result preview, sizes, buttons |
| `DownloadButton.jsx` | Saves the file |
| `ErrorMessage.jsx` | Friendly error banner |

**Other files:** `utils/validateImage.js` (browser-side checks), `utils/downloadImage.js` (download + safe filename), `utils/format.js` (sizes), `data/styles.js` (style names, descriptions, which sliders each shows), `services/sketchApi.js` (server calls, including reading JSON errors that arrive as Blobs).

**Behaviours worth knowing:**
- Classic Pencil is selected by default.
- **Stale results disappear:** changing the image, style, size, format, quality (JPG), or any slider removes the old result so it can never be mistaken for the current settings.
- Editing width/height keeps the other in step while the aspect ratio is locked, and shows red errors for invalid sizes before you generate.
- Pressing Generate again, or Cancel, aborts the running request.
- Temporary browser image URLs are always released, so memory does not leak.
- **Reset Workspace** clears everything without reloading the page.
- Supports dark mode and respects reduced-motion settings.

---

## 11. Project folder map

```
Sketchify Studio/
├── README.md                     ← this document
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── .env.example              ← all configurable limits
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py               ← creates the app, CORS, error handlers
│   │   ├── config.py             ← loads limits from environment
│   │   ├── schemas.py            ← response models and option rules
│   │   ├── errors.py             ← ApiError type
│   │   ├── api/routes.py         ← /api/health and /api/sketch
│   │   ├── services/
│   │   │   ├── image_service.py  ← safe decoding and resizing
│   │   │   ├── sketch_service.py ← picks the style, colour, validates, encodes
│   │   │   └── styles/           ← one file per style + _common.py (shared helpers)
│   │   └── utils/
│   │       ├── validators.py     ← parameter checks
│   │       └── sample.py         ← procedural sample scene (thumbnails and tests)
│   ├── scripts/make_thumbnails.py
│   └── tests/                    ← 100 tests
└── frontend/
    ├── package.json, vite.config.js, index.html
    ├── .env.example              ← VITE_API_BASE_URL
    ├── public/styles/            ← style thumbnails (generated by our algorithms)
    └── src/                      ← App.jsx, components, services, utils, data, index.css
```

---

## 12. How to run it

You need **Python 3.11+** and **Node.js 18+**.

### Backend

```bash
cd backend
python -m venv venv
venv/Scripts/activate          # Windows. On macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (in a second terminal)

```bash
cd frontend
npm install
cp .env.example .env           # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open **http://localhost:5173**. The backend's `FRONTEND_ORIGIN` must match the address you use in the browser (the default is `http://localhost:5173`).

### Rebuild the style thumbnails (optional)

```bash
cd backend
python scripts/make_thumbnails.py
```

### Production build and deployment

- Frontend: `npm run build`, then host the `dist/` folder (for example on Vercel). Set `VITE_API_BASE_URL` to the live backend address before building.
- Backend: run `uvicorn app.main:app` **without** `--reload`, set `FRONTEND_ORIGIN` to the real website address, pin dependency versions, and also limit request size at the web server or proxy. Use a host that supports Python and OpenCV.

---

## 13. Testing

```bash
cd backend
python -m pytest
```

Currently **100 tests pass**. They cover:

- **Health:** the endpoint answers.
- **Upload validation:** renamed text/PDF files, WebP, empty, corrupt, mismatched type, oversized, too small, too large, over the pixel limit, animated PNG, transparent PNG.
- **Parameters:** bad style, format, quality, width/height, aspect-ratio flag, options JSON, missing fields.
- **All eight styles:** valid output, correct size, not blank, visually different from each other, work when enlarged/shrunk, work on flat/black/white images, every slider extreme, and **dark photos do not give a blank result**.
- **Colour:** every style gives a real 3-channel colour image; strength 0 is grey; colour options are validated.
- **Output:** PNG and JPG signatures, content types, filenames, headers, JPG quality changes file size, PNG ignores quality, aspect ratio.
- **Robustness:** internal crashes return a clean 500 without leaking details; CORS headers.

The website was checked by hand in a browser: upload, choose styles, generate, stale-result removal, and a dark tall photo through Line Art. It has no automated UI tests.

---

## 14. Problems we hit and how we fixed them

| Problem | Cause | Fix |
|---|---|---|
| Line Art returned a **blank white image** for a dark 2252×4000 photo | Edge thresholds had a fixed minimum that a dark photo never reached; then the speck-remover (whose size limit grew with image *area*) deleted what was left | Stretch brightness before edge detection; base the speck limit on line *length* |
| Edges missing on bright images | Thresholds derived from median brightness | Use gradient-percentile thresholds (section 4.5) |
| Charcoal looked mid-grey everywhere | Light areas were being counted as shadow | Re-map tones so light areas stay bare paper |
| Cartoon Sketch was only grey | Styles only produced grey | Added the colour mode (section 6) |
| Wide screens had huge empty margins and tall photos looked tiny | Single narrow column | Two-column workspace with height-limited previews |

---

## 15. Limitations and future ideas

**Honest limitations**
- These are algorithmic approximations of art styles, not real hand-drawn art. Results depend on the photo; settings may need adjusting.
- Cartoon colour shows banding in smooth gradients.
- Very large images (25 MP) take several seconds, especially Cartoon and Charcoal (bilateral filters).
- Style thumbnails come from a drawn sample scene, not a real photograph.
- There are no automated frontend tests, and nothing has been deployed yet.

**Possible future work:** before/after comparison slider, side-by-side style comparison, batch conversion with ZIP download, crop/rotate, more styles (watercolour, stipple), and speed benchmarks.

---

## 16. Glossary

| Term | Plain meaning |
|---|---|
| Pixel | One tiny dot of a digital image |
| Grayscale | A picture with only brightness, no colour |
| Kernel / sigma | How wide a blur reaches |
| Gradient | How fast brightness changes between neighbouring pixels (high at edges) |
| Edge | A boundary where brightness changes suddenly |
| Threshold | A cut-off number that separates "yes" from "no" |
| Percentile | The value below which a given percentage of numbers fall (92nd percentile = bigger than 92% of values) |
| Posterise | Reduce the number of different tones |
| Anti-aliasing | Softening jagged edges so lines look smooth |
| MIME type | A label such as `image/png` saying what kind of file something is |
| EXIF | Extra information stored in photos, such as rotation |
| CORS | Browser rule that decides which website addresses may call the server |
| REST API | A way for the website to ask the server to do work using web requests |
| Blob | Raw file data held in the browser, here the sketch image |
| PNG | Lossless image format (perfect quality, bigger files) |
| JPG / JPEG | Compressed format (smaller files, quality slider) |
| Decompression bomb | A tiny file that expands into a gigantic image to crash a server |

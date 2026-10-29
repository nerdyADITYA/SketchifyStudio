from . import (
    cartoon_sketch,
    charcoal,
    classic_pencil,
    crosshatch,
    dark_pencil,
    fine_pencil,
    ink_outline,
    line_art,
)

SKETCH_STYLES = {
    "classic_pencil": classic_pencil.generate,
    "fine_pencil": fine_pencil.generate,
    "dark_pencil": dark_pencil.generate,
    "charcoal": charcoal.generate,
    "ink_outline": ink_outline.generate,
    "line_art": line_art.generate,
    "crosshatch": crosshatch.generate,
    "cartoon_sketch": cartoon_sketch.generate,
}

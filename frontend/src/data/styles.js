export const DEFAULT_STYLE = "classic_pencil";

export const SKETCH_STYLES = [
  {
    id: "classic_pencil",
    name: "Classic Pencil",
    description: "Soft shading with natural tonal transitions.",
    controls: ["intensity", "shading", "contrast"],
  },
  {
    id: "fine_pencil",
    name: "Fine Pencil",
    description: "Delicate lines and subtle shading.",
    controls: ["intensity", "detail", "shading", "contrast"],
  },
  {
    id: "dark_pencil",
    name: "Dark Pencil",
    description: "Bold strokes and strong contrast.",
    controls: ["intensity", "shading", "contrast", "detail"],
  },
  {
    id: "charcoal",
    name: "Charcoal",
    description: "Deep shadows and broad tonal regions.",
    controls: ["intensity", "shading", "contrast", "detail"],
  },
  {
    id: "ink_outline",
    name: "Ink Outline",
    description: "Clean black outlines, minimal shading.",
    controls: ["line_thickness", "detail", "intensity", "contrast"],
  },
  {
    id: "line_art",
    name: "Line Art",
    description: "Minimalist, simplified outlines.",
    controls: ["line_thickness", "detail", "intensity"],
  },
  {
    id: "crosshatch",
    name: "Crosshatch",
    description: "Intersecting strokes that follow the shadows.",
    controls: ["shading", "line_thickness", "intensity", "contrast", "detail"],
  },
  {
    id: "cartoon_sketch",
    name: "Cartoon Sketch",
    description: "Simplified tones with strong outlines.",
    controls: ["detail", "line_thickness", "intensity", "contrast"],
  },
];

export const CONTROL_LABELS = {
  intensity: { label: "Sketch intensity", hint: "Strength of the overall effect" },
  line_thickness: { label: "Line thickness", hint: "Width of outlines and strokes" },
  contrast: { label: "Contrast", hint: "Separation between dark and light" },
  detail: { label: "Detail level", hint: "Amount of fine detail kept" },
  shading: { label: "Shading strength", hint: "Intensity of tonal shading" },
};

export const DEFAULT_CONTROL_VALUE = 50;

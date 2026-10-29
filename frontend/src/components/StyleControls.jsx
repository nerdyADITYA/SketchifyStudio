import { RotateCcw } from "lucide-react";
import { CONTROL_LABELS, DEFAULT_CONTROL_VALUE, SKETCH_STYLES } from "../data/styles";

export default function StyleControls({ styleId, options, onChange, onReset, disabled }) {
  const style = SKETCH_STYLES.find((s) => s.id === styleId);
  if (!style) return null;
  const hasChanges = [...style.controls, "color_mode", "color_strength"].some((key) => options[key] !== undefined);
  const colorMode = options.color_mode ?? "grayscale";
  const colorStrength = options.color_strength ?? 100;

  return (
    <div className="settings-panel">
      <div className="panel-head">
        <h3>Fine-tune {style.name}</h3>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onReset} disabled={disabled || !hasChanges}>
          <RotateCcw size={14} aria-hidden="true" /> Reset
        </button>
      </div>
      <div className="slider-grid">
        <div className="field">
          <span>Colour</span>
          <div className="segmented" role="radiogroup" aria-label="Colour mode">
            {[
              ["grayscale", "Black & white"],
              ["color", "Original colours"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={colorMode === value}
                className={colorMode === value ? "active" : ""}
                disabled={disabled}
                onClick={() => onChange("color_mode", value)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        {colorMode === "color" && (
          <label className="field">
            <span>
              Colour strength <span className="muted">· {colorStrength}</span>
            </span>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              value={colorStrength}
              disabled={disabled}
              onChange={(e) => onChange("color_strength", Number(e.target.value))}
            />
            <small className="muted">How strongly the photo's colours show</small>
          </label>
        )}
        {style.controls.map((key) => {
          const value = options[key] ?? DEFAULT_CONTROL_VALUE;
          const meta = CONTROL_LABELS[key];
          return (
            <label className="field" key={key}>
              <span>
                {meta.label} <span className="muted">· {value}</span>
              </span>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={value}
                disabled={disabled}
                aria-describedby={`hint-${key}`}
                onChange={(e) => onChange(key, Number(e.target.value))}
              />
              <small id={`hint-${key}`} className="muted">{meta.hint}</small>
            </label>
          );
        })}
      </div>
    </div>
  );
}

export default function OutputSettings({
  width,
  height,
  preserveAspectRatio,
  format,
  quality,
  errors,
  disabled,
  onWidthChange,
  onHeightChange,
  onPreserveChange,
  onFormatChange,
  onQualityChange,
}) {
  const isPng = format === "png";

  return (
    <div className="settings-panel">
      <div className="field-row">
        <label className="field">
          <span>Width (px)</span>
          <input
            type="number"
            inputMode="numeric"
            min="1"
            step="1"
            value={width}
            disabled={disabled}
            aria-invalid={Boolean(errors.width)}
            onChange={(e) => onWidthChange(e.target.value)}
          />
        </label>
        <label className="field">
          <span>Height (px)</span>
          <input
            type="number"
            inputMode="numeric"
            min="1"
            step="1"
            value={height}
            disabled={disabled}
            aria-invalid={Boolean(errors.height)}
            onChange={(e) => onHeightChange(e.target.value)}
          />
        </label>
      </div>

      <label className="check">
        <input
          type="checkbox"
          checked={preserveAspectRatio}
          disabled={disabled}
          onChange={(e) => onPreserveChange(e.target.checked)}
        />
        <span>Preserve aspect ratio</span>
      </label>

      {errors.dimensions && <p className="field-error" role="alert">{errors.dimensions}</p>}
      {!errors.dimensions && width > 0 && height > 0 && (
        <p className="muted small">Final output: <strong>{width} × {height} px</strong></p>
      )}

      <div className="field-row">
        <label className="field">
          <span>Output format</span>
          <select value={format} disabled={disabled} onChange={(e) => onFormatChange(e.target.value)}>
            <option value="png">PNG</option>
            <option value="jpg">JPG</option>
          </select>
        </label>

        <label className="field">
          <span>JPEG quality {isPng ? "" : `· ${quality}%`}</span>
          <input
            type="range"
            min="10"
            max="100"
            step="1"
            value={quality}
            disabled={disabled || isPng}
            onChange={(e) => onQualityChange(Number(e.target.value))}
          />
        </label>
      </div>
      {isPng && <p className="muted small">PNG is lossless. JPEG quality settings do not apply.</p>}
    </div>
  );
}

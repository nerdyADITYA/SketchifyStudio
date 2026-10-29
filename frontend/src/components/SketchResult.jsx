import { RotateCcw } from "lucide-react";
import ImagePreview from "./ImagePreview";
import DownloadButton from "./DownloadButton";
import { formatBytes } from "../utils/format";

export default function SketchResult({ result, previewUrl, onReset }) {
  if (!result || !previewUrl) return null;
  return (
    <section className="card" aria-labelledby="result-heading">
      <h2 id="result-heading" className="section-title">Generated result</h2>
      <ImagePreview
        src={previewUrl}
        alt={`${result.styleName} sketch`}
        width={result.width}
        height={result.height}
      />
      <p className="result-meta">
        <span>Style: <strong>{result.styleName}</strong></span>
        <span>Output: <strong>{result.width} × {result.height} px</strong></span>
        <span>Size: <strong>{formatBytes(result.blob.size)}</strong></span>
        <span>Format: <strong>{result.format.toUpperCase()}</strong></span>
      </p>
      <div className="actions">
        <DownloadButton blob={result.blob} filename={result.filename} />
        <button type="button" className="btn btn-ghost" onClick={onReset}>
          <RotateCcw size={16} aria-hidden="true" /> Reset Workspace
        </button>
      </div>
    </section>
  );
}

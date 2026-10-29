import { formatBytes } from "../utils/format";

export default function ImageInfo({ info, output, preserveAspectRatio }) {
  if (!info) return null;
  return (
    <div className="info-grid">
      <dl>
        <div><dt>Filename</dt><dd title={info.name}>{info.name}</dd></div>
        <div><dt>Format</dt><dd>{info.format}</dd></div>
        <div><dt>Dimensions</dt><dd>{info.width} × {info.height} px</dd></div>
        <div><dt>File size</dt><dd>{formatBytes(info.size)}</dd></div>
      </dl>
      {output && (
        <dl>
          <div><dt>Output width</dt><dd>{output.width || "—"} px</dd></div>
          <div><dt>Output height</dt><dd>{output.height || "—"} px</dd></div>
          <div><dt>Aspect ratio</dt><dd>{preserveAspectRatio ? "Preserved" : "Free"}</dd></div>
        </dl>
      )}
    </div>
  );
}

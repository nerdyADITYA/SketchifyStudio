import { Download } from "lucide-react";
import { downloadImage } from "../utils/downloadImage";

export default function DownloadButton({ blob, filename, disabled }) {
  return (
    <button
      type="button"
      className="btn btn-primary"
      disabled={disabled || !blob}
      onClick={() => downloadImage(blob, filename)}
    >
      <Download size={16} aria-hidden="true" /> Download Sketch
    </button>
  );
}

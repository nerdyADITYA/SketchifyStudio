import { useRef, useState } from "react";
import { ImagePlus, UploadCloud } from "lucide-react";

export default function UploadZone({ onFile, compact = false, disabled = false }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const open = () => {
    if (!disabled) inputRef.current?.click();
  };

  const handleFiles = (files) => {
    const file = files && files[0];
    if (file) onFile(file);
  };

  return (
    <div
      className={`upload-zone${dragging ? " dragging" : ""}${compact ? " compact" : ""}`}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload an image. Drag and drop, or press Enter to browse files."
      aria-disabled={disabled}
      onClick={open}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          open();
        }
      }}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (!disabled) handleFiles(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        hidden
        accept=".jpg,.jpeg,.png,image/jpeg,image/png"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = ""; // allow re-selecting the same file
        }}
      />
      {compact ? (
        <>
          <ImagePlus size={20} aria-hidden="true" />
          <span>Drop a new image or <u>browse</u> to replace</span>
        </>
      ) : (
        <>
          <UploadCloud size={40} aria-hidden="true" />
          <p className="upload-title">Drag and drop your image</p>
          <p className="muted">or</p>
          <span className="btn btn-primary">Browse Files</span>
          <p className="muted small">JPG / JPEG / PNG · Maximum 10 MB</p>
        </>
      )}
    </div>
  );
}

export default function ImagePreview({ src, alt, label, width, height }) {
  return (
    <figure className="image-preview">
      {label && <figcaption className="eyebrow">{label}</figcaption>}
      <div className="preview-frame">
        {src ? (
          <img src={src} alt={alt} width={width} height={height} />
        ) : (
          <div className="preview-empty muted">No image</div>
        )}
      </div>
    </figure>
  );
}

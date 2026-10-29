export function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function scaledHeight(width, original) {
  return Math.round((width / original.width) * original.height);
}

export function scaledWidth(height, original) {
  return Math.round((height / original.height) * original.width);
}

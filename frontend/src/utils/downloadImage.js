export function downloadImage(blob, filename) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = objectUrl;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  setTimeout(() => {
    URL.revokeObjectURL(objectUrl);
  }, 1000);
}

/** "My Photo (1).jpg" + "png" -> "My_Photo_1_sketch.png" */
export function buildFilename(originalName, format) {
  const stem = (originalName || "")
    .replace(/\.[^.]*$/, "")
    .replace(/[^A-Za-z0-9_-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 60);
  return `${stem || "image"}_sketch.${format === "png" ? "png" : "jpg"}`;
}

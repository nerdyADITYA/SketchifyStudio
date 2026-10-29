import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

export class CancelledError extends Error {
  constructor() {
    super("Request cancelled.");
    this.name = "CancelledError";
  }
}

async function messageFromError(error) {
  if (axios.isCancel(error)) return null;

  if (error.code === "ECONNABORTED") {
    return "The request timed out. Try a smaller output size.";
  }

  if (!error.response) {
    return "Cannot reach the server. Make sure the backend is running.";
  }

  // The success type is "blob", so JSON error bodies arrive as Blobs too.
  const { data, status } = error.response;
  try {
    const text = data instanceof Blob ? await data.text() : JSON.stringify(data);
    const parsed = JSON.parse(text);
    if (parsed?.error?.message) return parsed.error.message;
  } catch {
    /* fall through to the generic message */
  }
  return `The server returned an error (${status}).`;
}

export async function generateSketch({
  file,
  style,
  width,
  height,
  preserveAspectRatio,
  format,
  quality,
  options,
  signal,
}) {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("style", style);
  formData.append("width", String(width));
  formData.append("height", String(height));
  formData.append("preserve_aspect_ratio", String(preserveAspectRatio));
  formData.append("format", format);
  formData.append("quality", String(quality));

  if (options && Object.keys(options).length > 0) {
    formData.append("options", JSON.stringify(options));
  }

  let response;
  try {
    response = await api.post("/api/sketch", formData, {
      responseType: "blob",
      signal,
    });
  } catch (error) {
    const message = await messageFromError(error);
    if (message === null) throw new CancelledError();
    throw new Error(message);
  }

  const contentType = response.headers["content-type"] || "";
  const outWidth = Number(response.headers["x-output-width"]);
  const outHeight = Number(response.headers["x-output-height"]);

  if (!/^image\/(png|jpeg)/.test(contentType)) {
    throw new Error("The server returned an unexpected response.");
  }
  if (!Number.isInteger(outWidth) || !Number.isInteger(outHeight) || outWidth < 1 || outHeight < 1) {
    throw new Error("The server returned invalid image dimensions.");
  }

  return { blob: response.data, contentType, width: outWidth, height: outHeight };
}

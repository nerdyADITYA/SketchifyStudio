import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Wand2 } from "lucide-react";

import Header from "./components/Header";
import Footer from "./components/Footer";
import UploadZone from "./components/UploadZone";
import ImageInfo from "./components/ImageInfo";
import ImagePreview from "./components/ImagePreview";
import SketchStyleSelector from "./components/SketchStyleSelector";
import OutputSettings from "./components/OutputSettings";
import StyleControls from "./components/StyleControls";
import ProcessingStatus from "./components/ProcessingStatus";
import SketchResult from "./components/SketchResult";
import ErrorMessage from "./components/ErrorMessage";

import { DEFAULT_STYLE, SKETCH_STYLES } from "./data/styles";
import { CancelledError, generateSketch } from "./services/sketchApi";
import { validateImage, MAX_DIMENSION } from "./utils/validateImage";
import { buildFilename } from "./utils/downloadImage";
import { scaledHeight, scaledWidth } from "./utils/format";

const MIN_OUTPUT = 16;
const MAX_OUTPUT_PIXELS = 25_000_000;
const DEFAULT_QUALITY = 90;

function toDimension(raw) {
  if (raw === "") return "";
  const n = Math.floor(Number(raw));
  return Number.isFinite(n) ? n : "";
}

export default function App() {
  const [originalFile, setOriginalFile] = useState(null);
  const [originalPreview, setOriginalPreview] = useState(null);
  const [imageInfo, setImageInfo] = useState(null);

  const [sketchStyle, setSketchStyle] = useState(DEFAULT_STYLE);

  const [width, setWidth] = useState(0);
  const [height, setHeight] = useState(0);
  const [preserveAspectRatio, setPreserveAspectRatio] = useState(true);

  const [outputFormat, setOutputFormat] = useState("png");
  const [quality, setQuality] = useState(DEFAULT_QUALITY);

  const [styleOptions, setStyleOptions] = useState({});
  const [result, setResult] = useState(null);
  const [sketchPreview, setSketchPreview] = useState(null);

  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState("");

  const abortRef = useRef(null);
  const resultRef = useRef(null);

  // Object URLs are created and revoked in effects so they never leak.
  useEffect(() => {
    if (!originalFile) {
      setOriginalPreview(null);
      return undefined;
    }
    const url = URL.createObjectURL(originalFile);
    setOriginalPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [originalFile]);

  useEffect(() => {
    if (!result) {
      setSketchPreview(null);
      return undefined;
    }
    const url = URL.createObjectURL(result.blob);
    setSketchPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [result]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const activeStyle = SKETCH_STYLES.find((s) => s.id === sketchStyle);

  // Only options that the selected style exposes (and the user changed) are sent.
  const activeOptions = useMemo(() => {
    const picked = {};
    for (const key of [...activeStyle.controls, "color_mode", "color_strength"]) {
      if (styleOptions[key] !== undefined) picked[key] = styleOptions[key];
    }
    if (picked.color_mode !== "color") delete picked.color_strength;
    return picked;
  }, [activeStyle, styleOptions]);

  const dimensionErrors = useMemo(() => {
    const errors = {};
    if (!imageInfo) return errors;
    if (!Number.isInteger(width) || width <= 0) errors.width = true;
    if (!Number.isInteger(height) || height <= 0) errors.height = true;
    if (errors.width || errors.height) {
      errors.dimensions = "Enter whole-number dimensions greater than zero.";
    } else if (width < MIN_OUTPUT || height < MIN_OUTPUT) {
      errors.dimensions = `Output must be at least ${MIN_OUTPUT} × ${MIN_OUTPUT} px.`;
    } else if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
      errors.dimensions = `Width and height can be at most ${MAX_DIMENSION} px.`;
    } else if (width * height > MAX_OUTPUT_PIXELS) {
      errors.dimensions = "Output exceeds the 25 megapixel limit.";
    }
    return errors;
  }, [imageInfo, width, height]);

  const hasDimensionError = Boolean(dimensionErrors.dimensions);

  // Anything that changes what the server would produce makes an existing result stale.
  const outputKey = useMemo(
    () =>
      JSON.stringify([
        originalFile?.name,
        originalFile?.size,
        originalFile?.lastModified,
        sketchStyle,
        width,
        height,
        preserveAspectRatio,
        outputFormat,
        outputFormat === "jpg" ? quality : null,
        activeOptions,
      ]),
    [originalFile, sketchStyle, width, height, preserveAspectRatio, outputFormat, quality, activeOptions],
  );

  useEffect(() => {
    setResult((current) => (current && current.key !== outputKey ? null : current));
  }, [outputKey]);

  const cancelPending = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsProcessing(false);
  }, []);

  const handleFile = useCallback(
    async (file) => {
      setError("");
      cancelPending();
      try {
        const info = await validateImage(file);
        setOriginalFile(file);
        setImageInfo(info);
        setWidth(info.width);
        setHeight(info.height);
        setResult(null);
      } catch (err) {
        setError(err.message);
      }
    },
    [cancelPending],
  );

  const handleWidthChange = (raw) => {
    const value = toDimension(raw);
    setWidth(value);
    if (preserveAspectRatio && imageInfo && value > 0) setHeight(scaledHeight(value, imageInfo));
  };

  const handleHeightChange = (raw) => {
    const value = toDimension(raw);
    setHeight(value);
    if (preserveAspectRatio && imageInfo && value > 0) setWidth(scaledWidth(value, imageInfo));
  };

  const handlePreserveChange = (checked) => {
    setPreserveAspectRatio(checked);
    if (checked && imageInfo && width > 0) setHeight(scaledHeight(width, imageInfo));
  };

  const handleStyleChange = (id) => {
    setSketchStyle(id);
    setError("");
  };

  const handleOptionChange = (key, value) => {
    setStyleOptions((prev) => ({ ...prev, [key]: value }));
  };

  const handleOptionsReset = () => {
    setStyleOptions((prev) => {
      const next = { ...prev };
      for (const key of [...activeStyle.controls, "color_mode", "color_strength"]) delete next[key];
      return next;
    });
  };

  const handleGenerate = async () => {
    if (!originalFile || isProcessing || hasDimensionError) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const requestKey = outputKey;
    setError("");
    setResult(null);
    setIsProcessing(true);

    try {
      const data = await generateSketch({
        file: originalFile,
        style: sketchStyle,
        width,
        height,
        preserveAspectRatio,
        format: outputFormat,
        quality,
        options: activeOptions,
        signal: controller.signal,
      });

      setResult({
        key: requestKey,
        blob: data.blob,
        width: data.width,
        height: data.height,
        format: outputFormat,
        styleName: activeStyle.name,
        filename: buildFilename(originalFile.name, outputFormat),
      });
      requestAnimationFrame(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch (err) {
      if (!(err instanceof CancelledError)) setError(err.message);
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
        setIsProcessing(false);
      }
    }
  };

  const handleReset = () => {
    cancelPending();
    setOriginalFile(null);
    setImageInfo(null);
    setSketchStyle(DEFAULT_STYLE);
    setWidth(0);
    setHeight(0);
    setPreserveAspectRatio(true);
    setOutputFormat("png");
    setQuality(DEFAULT_QUALITY);
    setStyleOptions({});
    setResult(null);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const canGenerate = Boolean(originalFile) && !isProcessing && !hasDimensionError;

  return (
    <>
      <Header />
      <main className={`container${imageInfo ? " wide" : ""}`}>
        <section className="hero">
          <h1>Turn Your Photos into Art</h1>
          <p className="muted">Explore eight unique sketch styles, then export as PNG or JPG.</p>
        </section>

        <ErrorMessage message={error} onDismiss={() => setError("")} />

        <section className="card" aria-labelledby="upload-heading">
          <h2 id="upload-heading" className="section-title">1 · Upload</h2>
          <UploadZone onFile={handleFile} compact={Boolean(originalFile)} disabled={isProcessing} />
        </section>

        {imageInfo && (
          <div className="workspace">
            <div className="col col-preview">
            <section className="card" aria-labelledby="original-heading">
              <h2 id="original-heading" className="section-title">Original image</h2>
              <div className="split">
                <ImagePreview
                  src={originalPreview}
                  alt="Original upload"
                  width={imageInfo.width}
                  height={imageInfo.height}
                />
                <ImageInfo
                  info={imageInfo}
                  output={{ width, height }}
                  preserveAspectRatio={preserveAspectRatio}
                />
              </div>
            </section>

            <div ref={resultRef}>
              <SketchResult result={result} previewUrl={sketchPreview} onReset={handleReset} />
            </div>
            </div>

            <div className="col col-controls">
            <section className="card" aria-labelledby="style-heading">
              <h2 id="style-heading" className="section-title">2 · Choose your sketch style</h2>
              <SketchStyleSelector selected={sketchStyle} onSelect={handleStyleChange} disabled={isProcessing} />
              <StyleControls
                styleId={sketchStyle}
                options={styleOptions}
                onChange={handleOptionChange}
                onReset={handleOptionsReset}
                disabled={isProcessing}
              />
            </section>

            <section className="card" aria-labelledby="output-heading">
              <h2 id="output-heading" className="section-title">3 · Output settings</h2>
              <OutputSettings
                width={width}
                height={height}
                preserveAspectRatio={preserveAspectRatio}
                format={outputFormat}
                quality={quality}
                errors={dimensionErrors}
                disabled={isProcessing}
                onWidthChange={handleWidthChange}
                onHeightChange={handleHeightChange}
                onPreserveChange={handlePreserveChange}
                onFormatChange={setOutputFormat}
                onQualityChange={setQuality}
              />
              <div className="generate-row">
                {isProcessing ? (
                  <ProcessingStatus onCancel={cancelPending} />
                ) : (
                  <button type="button" className="btn btn-primary btn-lg" disabled={!canGenerate} onClick={handleGenerate}>
                    <Wand2 size={18} aria-hidden="true" /> Generate Sketch
                  </button>
                )}
              </div>
            </section>

            {!result && (
              <div className="actions center">
                <button type="button" className="btn btn-ghost" onClick={handleReset}>
                  Reset Workspace
                </button>
              </div>
            )}
            </div>
          </div>
        )}
      </main>
      <Footer />
    </>
  );
}

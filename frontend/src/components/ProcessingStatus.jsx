export default function ProcessingStatus({ onCancel }) {
  return (
    <div className="processing" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>Sketching your image…</span>
      <button type="button" className="btn btn-ghost btn-sm" onClick={onCancel}>
        Cancel
      </button>
    </div>
  );
}

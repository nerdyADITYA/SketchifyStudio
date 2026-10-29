import { AlertCircle, X } from "lucide-react";

export default function ErrorMessage({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="error-message" role="alert">
      <AlertCircle size={18} aria-hidden="true" />
      <span>{message}</span>
      {onDismiss && (
        <button type="button" className="icon-btn" onClick={onDismiss} aria-label="Dismiss error">
          <X size={16} />
        </button>
      )}
    </div>
  );
}

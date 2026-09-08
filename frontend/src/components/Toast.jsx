export default function Toast({ message, type = "success", onClose }) {
  if (!message) return null;

  return (
    <div className={`toast toast-${type}`} role="status">
      <span className="toast-dot" />
      <span>{message}</span>
      {onClose && (
        <button
          type="button"
          className="toast-close"
          onClick={onClose}
          aria-label="Bildirimi kapat"
        >
          ×
        </button>
      )}
    </div>
  );
}

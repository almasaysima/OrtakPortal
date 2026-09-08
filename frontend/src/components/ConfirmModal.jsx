function ConfirmModal({
  dialog,
  onConfirm,
  onCancel,
}) {
  if (!dialog) {
    return null;
  }

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onCancel();
        }
      }}
    >
      <div
        className="modal-shell confirm-modal-shell"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-modal-title"
      >
        <div className="modal-header">
          <div>
            <span className="modal-eyebrow">
              Onay Gerekiyor
            </span>

            <h2 id="confirm-modal-title">
              {dialog.title}
            </h2>
          </div>

          <button
            type="button"
            className="modal-close"
            onClick={onCancel}
            aria-label="Kapat"
          >
            ×
          </button>
        </div>

        <div className="modal-body">
          <p className="confirm-dialog-message">
            {dialog.message}
          </p>

          <div className="admin-form-actions confirm-dialog-actions">
            <button
              className="btn btn-light"
              type="button"
              onClick={onCancel}
            >
              Vazgeç
            </button>

            <button
              className={
                dialog.danger
                  ? "btn btn-danger"
                  : "btn btn-primary"
              }
              type="button"
              onClick={onConfirm}
            >
              {dialog.confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;

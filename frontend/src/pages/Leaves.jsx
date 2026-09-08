import ConfirmModal from "../components/ConfirmModal";
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import Sidebar from "../components/Sidebar";
import Toast from "../components/Toast";
import { useAuth } from "../context/AuthContext";

function Leaves() {
  const {
    user,
    authLoading,
  } = useAuth();

  const [leaves, setLeaves] = useState([]);
  const [pendingLeaves, setPendingLeaves] = useState([]);

  const [loading, setLoading] = useState(false);
  const [pendingLoading, setPendingLoading] = useState(false);

  const [formLoading, setFormLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [pendingError, setPendingError] = useState("");

  const [form, setForm] = useState({
    start_date: "",
    end_date: "",
    reason: "",
  });

  const loadLeaves = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/leaves/my", {
        credentials: "include",
      });

      const data = await response.json();

      if (!response.ok) {
        setError(
          data.error ||
            "İzin kayıtları alınamadı."
        );
        setLeaves([]);
        return;
      }

      setLeaves(
        Array.isArray(data)
          ? data
          : []
      );
    } catch (err) {
      console.error(
        "İzin listeleme hatası:",
        err
      );

      setError(
        "İzin kayıtları alınırken hata oluştu."
      );

      setLeaves([]);
    } finally {
      setLoading(false);
    }
  };

  const loadPendingLeaves = async () => {
    setPendingLoading(true);
    setPendingError("");

    try {
      const response = await fetch(
        "/api/leaves/pending",
        {
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setPendingLeaves([]);
        setPendingError(
          data.error ||
            "Bekleyen izinler alınamadı."
        );
        return;
      }

      const pendingData = Array.isArray(data)
        ? data
        : Array.isArray(data.requests)
        ? data.requests
        : [];

      setPendingLeaves(pendingData);
    } catch (err) {
      console.error(
        "Bekleyen izinler hatası:",
        err
      );

      setPendingLeaves([]);
      setPendingError(
        "Bekleyen izinler alınamadı."
      );
    } finally {
      setPendingLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading || !user) {
      return;
    }

    loadLeaves();
    loadPendingLeaves();
  }, [authLoading, user]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setFormLoading(true);

    try {
      const response = await fetch(
        "/api/leaves",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            start_date: form.start_date,
            end_date: form.end_date,
            reason: form.reason.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(
          data.error ||
            "İzin talebi oluşturulamadı."
        );
        return;
      }

      setForm({
        start_date: "",
        end_date: "",
        reason: "",
      });

      setSuccess(
        data.message ||
          "İzin talebiniz başarıyla oluşturuldu."
      );

      await loadLeaves();
      await loadPendingLeaves();
    } catch (err) {
      console.error(
        "İzin oluşturma hatası:",
        err
      );

      setError(
        "Sunucuya bağlanırken hata oluştu."
      );
    } finally {
      setFormLoading(false);
    }
  };

  const [
    confirmDialog,
    setConfirmDialog,
  ] = useState(null);

  const requestConfirmation = ({
    title,
    message,
    confirmText,
    danger = false,
  }) =>
    new Promise((resolve) => {
      setConfirmDialog({
        title,
        message,
        confirmText,
        danger,
        resolve,
      });
    });

  const finishConfirmation = (
    result
  ) => {
    const resolve =
      confirmDialog?.resolve;

    setConfirmDialog(null);

    if (resolve) {
      resolve(result);
    }
  };


  const handleApprove = async (requestId) => {
    const confirmed =
      await requestConfirmation({
        title: "İzin Talebini Onayla",
        message: "Bu izin talebini onaylamak istediğinize emin misiniz?",
        confirmText: "Onayla",
        danger: false,
      });

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");
    setActionLoading(true);

    try {
      const response = await fetch(
        `/api/leaves/${requestId}/approve`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            note: "",
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(
          data.error ||
            "İzin talebi onaylanamadı."
        );
        return;
      }

      setSuccess(
        data.message ||
          "İzin talebi başarıyla onaylandı."
      );

      await loadPendingLeaves();
      await loadLeaves();
    } catch (err) {
      console.error(
        "İzin onaylama hatası:",
        err
      );

      setError(
        "İzin onaylanırken hata oluştu."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (requestId) => {
    const confirmed =
      await requestConfirmation({
        title: "İzin Talebini Reddet",
        message: "Bu izin talebini reddetmek istediğinize emin misiniz?",
        confirmText: "Reddet",
        danger: true,
      });

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");
    setActionLoading(true);

    try {
      const response = await fetch(
        `/api/leaves/${requestId}/reject`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            note: "",
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(
          data.error ||
            "İzin talebi reddedilemedi."
        );
        return;
      }

      setSuccess(
        data.message ||
          "İzin talebi reddedildi."
      );

      await loadPendingLeaves();
      await loadLeaves();
    } catch (err) {
      console.error(
        "İzin reddetme hatası:",
        err
      );

      setError(
        "İzin reddedilirken hata oluştu."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusText = (leave) => {
    if (leave.status === "approved") {
      return "Onaylandı";
    }

    if (leave.status === "rejected") {
      return "Reddedildi";
    }

    if (leave.status === "cancelled") {
      return "İptal edildi";
    }

    if (
      leave.approval_stage ===
      "manager_pending"
    ) {
      return "Yönetici onayı bekliyor";
    }

    if (
      leave.approval_stage ===
      "hr_pending"
    ) {
      return "İK onayı bekliyor";
    }

    if (
      leave.approval_stage ===
      "completed"
    ) {
      return "Tamamlandı";
    }

    return leave.status || "-";
  };

  const getApprovalStageText = (stage) => {
    if (stage === "manager_pending") {
      return "Yönetici";
    }

    if (stage === "hr_pending") {
      return "İK";
    }

    if (stage === "completed") {
      return "Tamamlandı";
    }

    return stage || "-";
  };

  const getApprovalStepState = (
    leave,
    step
  ) => {
    if (step === "request") {
      return "complete";
    }

    if (
      leave.status === "cancelled"
    ) {
      return "muted";
    }

    if (step === "manager") {
      if (
        leave.status === "rejected" &&
        leave.approval_stage ===
          "manager_pending"
      ) {
        return "rejected";
      }

      if (
        leave.status === "approved" ||
        leave.approval_stage ===
          "hr_pending" ||
        leave.approval_stage ===
          "completed"
      ) {
        return "complete";
      }

      if (
        leave.approval_stage ===
        "manager_pending"
      ) {
        return "current";
      }

      return "pending";
    }

    if (step === "hr") {
      if (
        leave.status === "rejected" &&
        leave.approval_stage !==
          "manager_pending"
      ) {
        return "rejected";
      }

      if (
        leave.status === "approved" ||
        leave.approval_stage ===
          "completed"
      ) {
        return "complete";
      }

      if (
        leave.approval_stage ===
        "hr_pending"
      ) {
        return "current";
      }

      return "pending";
    }

    return "pending";
  };

  const renderApprovalStepper = (
    leave
  ) => {
    const steps = [
      {
        key: "request",
        label: "Talep",
      },
      {
        key: "manager",
        label: "Yönetici",
      },
      {
        key: "hr",
        label: "İK",
      },
    ];

    return (
      <div
        className="approval-stepper"
        aria-label="İzin onay süreci"
      >
        {steps.map(
          (step, index) => {
            const state =
              getApprovalStepState(
                leave,
                step.key
              );

            return (
              <div
                className={`approval-step approval-step-${state}`}
                key={step.key}
              >
                <div className="approval-step-track">
                  <span className="approval-step-dot">
                    {state === "complete"
                      ? "✓"
                      : state === "rejected"
                      ? "×"
                      : index + 1}
                  </span>

                  {index <
                    steps.length - 1 && (
                    <span className="approval-step-line" />
                  )}
                </div>

                <span className="approval-step-label">
                  {step.label}
                </span>
              </div>
            );
          }
        )}
      </div>
    );
  };

  if (authLoading) {
    return (
      <div className="empty-state">
        Oturum kontrol ediliyor...
      </div>
    );
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  return (
    <div className="dashboard">
      <Sidebar />

      <main className="content">
        <section className="topbar">
          <div>
            <h1>İzinler</h1>

            <p>
              İzin taleplerini oluştur ve
              mevcut taleplerini takip et.
            </p>
          </div>

          <div className="user-badge">
            {user.department}
          </div>
        </section>

        {error && (
          <div className="alert-error">
            {error}
          </div>
        )}

        {success && (
          <div className="alert-success">
            {success}
          </div>
        )}

        <section className="card">
          <div className="card-header">
            <div>
              <h2>Yeni İzin Talebi</h2>

              <p>
                Yeni bir izin talebi oluştur.
              </p>
            </div>
          </div>

          <form className="leave-request-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="leave-start">
                Başlangıç Tarihi
              </label>

              <input
                id="leave-start"
                type="date"
                value={form.start_date}
                onChange={(event) =>
                  setForm({
                    ...form,
                    start_date:
                      event.target.value,
                  })
                }
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="leave-end">
                Bitiş Tarihi
              </label>

              <input
                id="leave-end"
                type="date"
                value={form.end_date}
                onChange={(event) =>
                  setForm({
                    ...form,
                    end_date:
                      event.target.value,
                  })
                }
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="leave-reason">
                İzin Açıklaması
              </label>

              <textarea
                id="leave-reason"
                value={form.reason}
                onChange={(event) =>
                  setForm({
                    ...form,
                    reason:
                      event.target.value,
                  })
                }
                placeholder="İzin talebinizle ilgili açıklama"
                required
              />
            </div>

            <button
              className="btn btn-primary"
              type="submit"
              disabled={formLoading}
            >
              {formLoading
                ? "Gönderiliyor..."
                : "İzin Talebi Oluştur"}
            </button>
          </form>
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <h2>Bekleyen İzinler</h2>

              <p>
                Onay işlemi bekleyen izin talepleri.
              </p>
            </div>
          </div>

          {pendingLoading ? (
            <div className="empty-state">
              Bekleyen izinler yükleniyor...
            </div>
          ) : pendingError ? (
            <div className="alert-error">
              {pendingError}
            </div>
          ) : pendingLeaves.length === 0 ? (
            <div className="empty-state">
              Bekleyen izin talebi bulunmuyor.
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Çalışan</th>
                    <th>Departman</th>
                    <th>Başlangıç</th>
                    <th>Bitiş</th>
                    <th>Açıklama</th>
                    <th>Aşama</th>
                    <th>İşlem</th>
                  </tr>
                </thead>

                <tbody>
                  {pendingLeaves.map(
                    (leave) => (
                      <tr
                        key={leave.id}
                      >
                        <td>
                          {leave.first_name || "-"}{" "}
                          {leave.last_name || ""}
                        </td>

                        <td>
                          {leave.department || "-"}
                        </td>

                        <td>
                          {leave.start_date}
                        </td>

                        <td>
                          {leave.end_date}
                        </td>

                        <td>
                          {leave.reason}
                        </td>

                        <td>
                          {getApprovalStageText(
                            leave.approval_stage
                          )}
                        </td>

                        <td>
                          <div className="action-row">
                            <button
                              className="btn btn-primary"
                              type="button"
                              disabled={
                                actionLoading
                              }
                              onClick={() =>
                                handleApprove(
                                  leave.id
                                )
                              }
                            >
                              Onayla
                            </button>

                            <button
                              className="btn btn-danger"
                              type="button"
                              disabled={
                                actionLoading
                              }
                              onClick={() =>
                                handleReject(
                                  leave.id
                                )
                              }
                            >
                              Reddet
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="card">
          <div className="card-header">
            <div>
              <h2>İzin Taleplerim</h2>

              <p>
                Daha önce oluşturduğun izin
                taleplerini görüntüle.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="empty-state">
              İzin kayıtları yükleniyor...
            </div>
          ) : leaves.length === 0 ? (
            <div className="empty-state rich-empty-state">
              <span className="empty-state-icon">
                İ
              </span>
              Henüz izin talebiniz bulunmuyor.
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Başlangıç</th>
                    <th>Bitiş</th>
                    <th>Açıklama</th>
                    <th>Durum</th>
                    <th>Onay Süreci</th>
                    <th>Yönetici</th>
                  </tr>
                </thead>

                <tbody>
                  {leaves.map(
                    (leave) => (
                      <tr
                        key={leave.id}
                      >
                        <td>
                          {leave.start_date}
                        </td>

                        <td>
                          {leave.end_date}
                        </td>

                        <td>
                          {leave.reason}
                        </td>

                        <td>
                          {getStatusText(
                            leave
                          )}
                        </td>

                        <td className="approval-stepper-cell">
                          {renderApprovalStepper(
                            leave
                          )}
                        </td>

                        <td>
                          {leave.manager
                            ? `${leave.manager.first_name || ""} ${leave.manager.last_name || ""}`.trim() ||
                              "-"
                            : "-"}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
        <ConfirmModal
          dialog={confirmDialog}
          onCancel={() =>
            finishConfirmation(false)
          }
          onConfirm={() =>
            finishConfirmation(true)
          }
        />

      </main>
    </div>
  );
}

export default Leaves;
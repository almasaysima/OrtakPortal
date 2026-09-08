import { useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";

import Sidebar from "../components/Sidebar";
import CollapsibleSection from "../components/CollapsibleSection";
import { useAuth } from "../context/AuthContext";


const DEPARTMENTS = [
  "Bilgi Teknolojileri",
  "Finans",
  "İnsan Kaynakları",
];

const EMPTY_USER_FORM = {
  username: "",
  email: "",
  first_name: "",
  last_name: "",
  department: "Bilgi Teknolojileri",
  role: "employee",
  password: "",
  new_password: "",
  manager_id: "",
};

const EMPTY_ANNOUNCEMENT_FORM = {
  title: "",
  content: "",
  department: "Genel",
};

const EMPTY_EVENT_FORM = {
  title: "",
  description: "",
  event_date: "",
  location: "",
  department: "Genel",
};


function Admin() {
  const {
    user,
    authLoading,
  } = useAuth();

  const [users, setUsers] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [events, setEvents] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [documents, setDocuments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [message, setMessage] = useState("");

  const [userForm, setUserForm] = useState(EMPTY_USER_FORM);
  const [editingUserId, setEditingUserId] = useState(null);

  const [announcementForm, setAnnouncementForm] =
    useState(EMPTY_ANNOUNCEMENT_FORM);
  const [editingAnnouncementId, setEditingAnnouncementId] =
    useState(null);

  const [eventForm, setEventForm] = useState(EMPTY_EVENT_FORM);
  const [editingEventId, setEditingEventId] = useState(null);

  const [leaveNote, setLeaveNote] = useState({});

  const [documentFile, setDocumentFile] = useState(null);
  const [documentCategory, setDocumentCategory] = useState("Genel");

  const [activeModal, setActiveModal] = useState(null);
  const [toast, setToast] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState(null);

  const isAdmin =
    String(user?.role || "").toLowerCase() === "admin";

  const managers = useMemo(
    () =>
      users.filter((item) => {
        if (userForm.department === "Bilgi Teknolojileri") {
          return item.role === "it_admin";
        }

        if (userForm.department === "Finans") {
          return item.role === "finance_admin";
        }

        if (userForm.department === "İnsan Kaynakları") {
          return item.role === "hr_admin";
        }

        return false;
      }),
    [users, userForm.department]
  );

  const requestJson = async (
    url,
    options = {}
  ) => {
    const response = await fetch(
      url,
      {
        credentials: "include",
        ...options,
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.error ||
        "İşlem gerçekleştirilemedi."
      );
    }

    return data;
  };

  const loadAll = async () => {
    setLoading(true);
    setPageError("");

    try {
      const [
        usersData,
        announcementsData,
        eventsData,
        leavesData,
        documentsData,
      ] = await Promise.all([
        requestJson("/api/users"),
        requestJson("/api/announcements"),
        requestJson("/api/events"),
        requestJson("/api/leaves/admin"),
        requestJson("/api/documents"),
      ]);

      setUsers(usersData);
      setAnnouncements(announcementsData);
      setEvents(eventsData);
      setLeaves(leavesData);
      setDocuments(documentsData);

    } catch (error) {
      console.error(
        "Admin veri hatası:",
        error
      );

      setPageError(
        error.message
      );

    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (
      !authLoading &&
      isAdmin
    ) {
      loadAll();
    }
  }, [authLoading, isAdmin]);

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

  if (!isAdmin) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  const clearFeedback = () => {
    setPageError("");
    setMessage("");
  };

  const showToast = (
    text,
    type = "success"
  ) => {
    setToast({
      text,
      type,
    });

    window.clearTimeout(
      window.__portalToastTimer
    );

    window.__portalToastTimer =
      window.setTimeout(() => {
        setToast(null);
      }, 2800);
  };

  const closeModal = () => {
    setActiveModal(null);
  };

  const openConfirmDialog = ({
    title,
    message,
    confirmText = "Sil",
    onConfirm,
  }) => {
    setConfirmDialog({
      title,
      message,
      confirmText,
      onConfirm,
    });
  };

  const closeConfirmDialog = () => {
    setConfirmDialog(null);
  };

  const confirmDelete = async () => {
    if (!confirmDialog?.onConfirm) {
      return;
    }

    const action = confirmDialog.onConfirm;
    closeConfirmDialog();
    await action();
  };

  const handleUserSubmit = async (
    event
  ) => {
    event.preventDefault();
    clearFeedback();

    try {
      if (editingUserId) {
        const payload = {
          ...userForm,
        };

        delete payload.password;

        await requestJson(
          `/api/users/${editingUserId}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
          }
        );

        showToast(
          "Kullanıcı başarıyla güncellendi."
        );

      } else {
        const payload = {
          ...userForm,
        };

        delete payload.new_password;

        await requestJson(
          "/api/users",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
          }
        );

        showToast(
          "Kullanıcı başarıyla oluşturuldu."
        );
      }

      setEditingUserId(null);
      setUserForm(EMPTY_USER_FORM);
      closeModal();
      await loadAll();

    } catch (error) {
      setPageError(
        error.message
      );
    }
  };

  const beginEditUser = (
    target
  ) => {
    setEditingUserId(
      target.id
    );

    setActiveModal("user");

    setUserForm({
      username: target.username,
      email: target.email,
      first_name: target.first_name,
      last_name: target.last_name,
      department: target.department,
      role: target.role,
      password: "",
      new_password: "",
      manager_id:
        target.manager_id || "",
    });

    document
      .getElementById("users")
      ?.scrollIntoView({
        behavior: "smooth",
      });
  };

  const handleDeleteUser = (userId) => {
    openConfirmDialog({
      title: "Kullanıcıyı Sil",
      message: "Bu kullanıcı kalıcı olarak silinecek. Bu işlemi gerçekleştirmek istediğinize emin misiniz?",
      confirmText: "Kullanıcıyı Sil",
      onConfirm: async () => {
        clearFeedback();
        try {
          await requestJson(`/api/users/${userId}`, { method: "DELETE" });
          showToast("Kullanıcı silindi.");
          await loadAll();
        } catch (error) {
          setPageError(error.message);
        }
      },
    });
  };

  const handleAnnouncementSubmit = async (
    event
  ) => {
    event.preventDefault();
    clearFeedback();

    try {
      const options = {
        method:
          editingAnnouncementId
            ? "PUT"
            : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          announcementForm
        ),
      };

      const url =
        editingAnnouncementId
          ? `/api/announcements/${editingAnnouncementId}`
          : "/api/announcements";

      await requestJson(
        url,
        options
      );

      setEditingAnnouncementId(
        null
      );

      setAnnouncementForm(
        EMPTY_ANNOUNCEMENT_FORM
      );

      closeModal();

      showToast(
        "Duyuru kaydedildi."
      );

      await loadAll();

    } catch (error) {
      setPageError(
        error.message
      );
    }
  };

  const handleDeleteAnnouncement = (announcementId) => {
    openConfirmDialog({
      title: "Duyuruyu Sil",
      message: "Bu duyuru kalıcı olarak silinecek. Devam etmek istediğinize emin misiniz?",
      confirmText: "Duyuruyu Sil",
      onConfirm: async () => {
        try {
          await requestJson(`/api/announcements/${announcementId}`, { method: "DELETE" });
          showToast("Duyuru silindi.");
          await loadAll();
        } catch (error) {
          setPageError(error.message);
        }
      },
    });
  };

  const handleEventSubmit = async (
    event
  ) => {
    event.preventDefault();
    clearFeedback();

    try {
      const options = {
        method:
          editingEventId
            ? "PUT"
            : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          eventForm
        ),
      };

      const url =
        editingEventId
          ? `/api/events/${editingEventId}`
          : "/api/events";

      await requestJson(
        url,
        options
      );

      setEditingEventId(null);
      setEventForm(
        EMPTY_EVENT_FORM
      );

      closeModal();

      showToast(
        "Etkinlik kaydedildi."
      );

      await loadAll();

    } catch (error) {
      setPageError(
        error.message
      );
    }
  };

  const handleDeleteEvent = (eventId) => {
    openConfirmDialog({
      title: "Etkinliği Sil",
      message: "Bu etkinlik kalıcı olarak silinecek. Devam etmek istediğinize emin misiniz?",
      confirmText: "Etkinliği Sil",
      onConfirm: async () => {
        try {
          await requestJson(`/api/events/${eventId}`, { method: "DELETE" });
          showToast("Etkinlik silindi.");
          await loadAll();
        } catch (error) {
          setPageError(error.message);
        }
      },
    });
  };

  const reviewLeave = async (
    leaveId,
    action
  ) => {
    clearFeedback();

    try {
      await requestJson(
        `/api/leaves/${leaveId}/${action}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            note:
              leaveNote[leaveId] || "",
          }),
        }
      );

      showToast(
        action === "approve"
          ? "İzin talebi onaylandı."
          : "İzin talebi reddedildi.",
        action === "approve"
          ? "success"
          : "error"
      );

      await loadAll();

    } catch (error) {
      setPageError(
        error.message
      );
    }
  };

  const handleDocumentUpload = async (
    event
  ) => {
    event.preventDefault();
    clearFeedback();

    if (!documentFile) {
      setPageError(
        "Bir dosya seçmelisiniz."
      );
      return;
    }

    const formData = new FormData();

    formData.append(
      "file",
      documentFile
    );

    formData.append(
      "category",
      documentCategory
    );

    try {
      const response = await fetch(
        "/api/documents",
        {
          method: "POST",
          credentials: "include",
          body: formData,
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.error ||
          "Dosya yüklenemedi."
        );
      }

      setDocumentFile(null);
      setDocumentCategory("Genel");
      showToast(
        "Dosya başarıyla yüklendi."
      );

      event.target.reset();

      await loadAll();

    } catch (error) {
      setPageError(
        error.message
      );
    }
  };

  const handleDeleteDocument = (documentId) => {
    openConfirmDialog({
      title: "Dosyayı Sil",
      message: "Bu dosya kalıcı olarak silinecek. Devam etmek istediğinize emin misiniz?",
      confirmText: "Dosyayı Sil",
      onConfirm: async () => {
        try {
          await requestJson(`/api/documents/${documentId}`, { method: "DELETE" });
          showToast("Dosya silindi.");
          await loadAll();
        } catch (error) {
          setPageError(error.message);
        }
      },
    });
  };

  return (
    <div className="dashboard">

      <Sidebar />

      <main className="content">

        <section className="topbar">

          <div>
            <h1>
              Admin Paneli
            </h1>

            <p>
              Kullanıcıları ve portal içeriklerini tek ekrandan yönet.
            </p>
          </div>

          <div className="user-badge">
            Genel Admin
          </div>

        </section>

        {pageError && (
          <div className="alert-error">
            {pageError}
          </div>
        )}

        {message && (
          <div className="alert-success">
            {message}
          </div>
        )}

        {toast && (
          <div
            className={`toast ${
              toast.type === "error"
                ? "toast-error"
                : "toast-success"
            }`}
          >
            <span className="toast-dot" />
            <span>{toast.text}</span>
          </div>
        )}

        {loading ? (
          <div className="card">
            Yükleniyor...
          </div>
        ) : (
          <>
            <div className="stats">
              <div className="stat-card">
                <span>Kullanıcılar</span>
                <strong>{users.length}</strong>
              </div>

              <div className="stat-card">
                <span>Duyurular</span>
                <strong>{announcements.length}</strong>
              </div>

              <div className="stat-card">
                <span>Etkinlikler</span>
                <strong>{events.length}</strong>
              </div>

              <div className="stat-card">
                <span>İzin Talepleri</span>
                <strong>{leaves.length}</strong>
              </div>
            </div>

            <div id="users">
              <CollapsibleSection
                title="Kullanıcı Yönetimi"
                subtitle="Kullanıcı oluştur, düzenle ve sil."
                count={users.length}
                defaultOpen={false}
              >

              <div className="section-toolbar">
                <div>
                  <strong>{users.length} kullanıcı</strong>
                  <span>Yeni kullanıcı oluşturabilir veya listedeki kullanıcıları düzenleyebilirsin.</span>
                </div>

                <button
                  className="btn btn-primary"
                  type="button"
                  onClick={() => {
                    setEditingUserId(null);
                    setUserForm(EMPTY_USER_FORM);
                    setActiveModal("user");
                  }}
                >
                  + Yeni Kullanıcı
                </button>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Kullanıcı</th>
                      <th>Ad Soyad</th>
                      <th>Departman</th>
                      <th>Rol</th>
                      <th>Yönetici</th>
                      <th>İşlem</th>
                    </tr>
                  </thead>

                  <tbody>
                    {users.map(
                      (item) => (
                        <tr key={item.id}>
                          <td>
                            {item.username}
                            <br />
                            <small>
                              {item.email}
                            </small>
                          </td>

                          <td>
                            {item.first_name}{" "}
                            {item.last_name}
                          </td>

                          <td>
                            {item.department ===
                            "Bilgi Teknolojileri"
                              ? "IT"
                              : item.department}
                          </td>

                          <td>
                            <span className="badge badge-red">
                              {item.role === "admin"
                                ? "Genel Admin"
                                : item.role === "hr_admin"
                                ? "İK Admin"
                                : item.role === "it_admin"
                                ? "IT Yöneticisi"
                                : item.role === "finance_admin"
                                ? "Finans Yöneticisi"
                                : "Çalışan"}
                            </span>
                          </td>

                          <td>
                            {item.manager_name ||
                              "-"}
                          </td>

                          <td>
                            <div className="action-row">
                              <button
                                className="btn btn-light"
                                type="button"
                                onClick={() =>
                                  beginEditUser(
                                    item
                                  )
                                }
                              >
                                Düzenle
                              </button>

                              {item.id !==
                                user.id && (
                                <button
                                  className="btn btn-danger"
                                  type="button"
                                  onClick={() =>
                                    handleDeleteUser(
                                      item.id
                                    )
                                  }
                                >
                                  Sil
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            
              </CollapsibleSection>
            </div>

            <div className="admin-accordion-stack">

              <div id="announcements">
              <CollapsibleSection
                title="Duyurular"
                subtitle="Genel veya departmana özel."
                count={announcements.length}
                defaultOpen={false}
              >

                <div className="section-toolbar compact">
                  <span>{announcements.length} duyuru</span>

                  <button
                    className="btn btn-primary"
                    type="button"
                    onClick={() => {
                      setEditingAnnouncementId(null);
                      setAnnouncementForm(
                        EMPTY_ANNOUNCEMENT_FORM
                      );
                      setActiveModal("announcement");
                    }}
                  >
                    + Yeni Duyuru
                  </button>
                </div>

                {announcements.map(
                  (announcement) => (
                    <div
                      className="content-item"
                      key={announcement.id}
                    >
                      <h3>
                        {announcement.title}
                      </h3>

                      <p>
                        {announcement.content}
                      </p>

                      <div className="item-meta">
                        <span className="badge badge-red">
                          {announcement.department ===
                          "Bilgi Teknolojileri"
                            ? "IT"
                            : announcement.department}
                        </span>
                      </div>

                      <div className="action-row admin-item-actions">
                        <button
                          className="btn btn-light"
                          type="button"
                          onClick={() => {
                            setEditingAnnouncementId(
                              announcement.id
                            );

                            setActiveModal(
                              "announcement"
                            );

                            setAnnouncementForm({
                              title:
                                announcement.title,
                              content:
                                announcement.content,
                              department:
                                announcement.department,
                            });
                          }}
                        >
                          Düzenle
                        </button>

                        <button
                          className="btn btn-danger"
                          type="button"
                          onClick={() =>
                            handleDeleteAnnouncement(
                              announcement.id
                            )
                          }
                        >
                          Sil
                        </button>
                      </div>
                    </div>
                  )
                )}
              
              </CollapsibleSection>
            </div>

              <div id="events">
              <CollapsibleSection
                title="Etkinlikler"
                subtitle="Portal etkinliklerini yönet."
                count={events.length}
                defaultOpen={false}
              >

                <div className="section-toolbar compact">
                  <span>{events.length} etkinlik</span>

                  <button
                    className="btn btn-primary"
                    type="button"
                    onClick={() => {
                      setEditingEventId(null);
                      setEventForm(
                        EMPTY_EVENT_FORM
                      );
                      setActiveModal("event");
                    }}
                  >
                    + Yeni Etkinlik
                  </button>
                </div>

                {events.map(
                  (item) => (
                    <div
                      className="content-item"
                      key={item.id}
                    >
                      <h3>{item.title}</h3>

                      <p>
                        {item.description}
                      </p>

                      <div className="item-meta">
                        <span className="badge badge-red">
                          {item.department ===
                          "Bilgi Teknolojileri"
                            ? "IT"
                            : item.department}
                        </span>

                        <span className="badge badge-gray">
                          {item.event_date}
                        </span>
                      </div>

                      <div className="action-row admin-item-actions">
                        <button
                          className="btn btn-light"
                          type="button"
                          onClick={() => {
                            setEditingEventId(
                              item.id
                            );

                            setActiveModal(
                              "event"
                            );

                            setEventForm({
                              title:
                                item.title,
                              description:
                                item.description,
                              event_date:
                                item.event_date
                                  ? item.event_date.slice(
                                      0,
                                      16
                                    )
                                  : "",
                              location:
                                item.location || "",
                              department:
                                item.department,
                            });
                          }}
                        >
                          Düzenle
                        </button>

                        <button
                          className="btn btn-danger"
                          type="button"
                          onClick={() =>
                            handleDeleteEvent(
                              item.id
                            )
                          }
                        >
                          Sil
                        </button>
                      </div>
                    </div>
                  )
                )}
              
              </CollapsibleSection>
            </div>

            </div>

            <div id="leaves">
              <CollapsibleSection
                title="İzin Talepleri"
                subtitle="Onay sürecindeki ve tamamlanan talepler."
                count={leaves.length}
                defaultOpen={false}
              >

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Çalışan</th>
                      <th>Departman</th>
                      <th>Tarih</th>
                      <th>Açıklama</th>
                      <th>Aşama</th>
                      <th>İşlem</th>
                    </tr>
                  </thead>

                  <tbody>
                    {leaves.map(
                      (leave) => (
                        <tr key={leave.id}>
                          <td>
                            {leave.first_name}{" "}
                            {leave.last_name}
                          </td>

                          <td>
                            {leave.department ===
                            "Bilgi Teknolojileri"
                              ? "IT"
                              : leave.department}
                          </td>

                          <td>
                            {leave.start_date}
                            <br />
                            {leave.end_date}
                          </td>

                          <td>
                            {leave.reason}
                          </td>

                          <td>
                            <span
                              className={`badge ${
                                leave.status ===
                                "approved"
                                  ? "badge-success"
                                  : leave.status ===
                                    "rejected"
                                  ? "badge-danger"
                                  : "badge-warning"
                              }`}
                            >
                              {leave.approval_stage ||
                                leave.status}
                            </span>
                          </td>

                          <td>
                            {leave.status ===
                            "pending" ? (
                              <div className="leave-review-box">
                                <input
                                  placeholder="Not"
                                  value={
                                    leaveNote[
                                      leave.id
                                    ] || ""
                                  }
                                  onChange={(event) =>
                                    setLeaveNote({
                                      ...leaveNote,
                                      [leave.id]:
                                        event.target.value,
                                    })
                                  }
                                />

                                <div className="action-row">
                                  <button
                                    className="btn btn-success"
                                    type="button"
                                    onClick={() =>
                                      reviewLeave(
                                        leave.id,
                                        "approve"
                                      )
                                    }
                                  >
                                    Onayla
                                  </button>

                                  <button
                                    className="btn btn-danger"
                                    type="button"
                                    onClick={() =>
                                      reviewLeave(
                                        leave.id,
                                        "reject"
                                      )
                                    }
                                  >
                                    Reddet
                                  </button>
                                </div>
                              </div>
                            ) : (
                              leave.hr_note ||
                              leave.manager_note ||
                              "-"
                            )}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            
              </CollapsibleSection>
            </div>

            <div id="documents">
              <CollapsibleSection
                title="Dosyalar"
                subtitle="MinIO üzerindeki şirket dosyaları."
                count={documents.length}
                defaultOpen={false}
              >

              <div className="section-toolbar compact">
                <span>{documents.length} dosya</span>

                <button
                  className="btn btn-primary"
                  type="button"
                  onClick={() =>
                    setActiveModal("document")
                  }
                >
                  + Dosya Yükle
                </button>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Dosya</th>
                      <th>Kategori</th>
                      <th>Yükleyen</th>
                      <th>Tarih</th>
                      <th>İşlem</th>
                    </tr>
                  </thead>

                  <tbody>
                    {documents.map(
                      (item) => (
                        <tr key={item.id}>
                          <td>
                            {item.file_name}
                          </td>

                          <td>
                            {item.category ||
                              "Genel"}
                          </td>

                          <td>
                            {item.uploaded_by ||
                              "-"}
                          </td>

                          <td>
                            {item.uploaded_at ||
                              "-"}
                          </td>

                          <td>
                            <div className="action-row">
                              <a
                                className="btn btn-light"
                                href={`/api/documents/${item.id}/download`}
                              >
                                İndir
                              </a>

                              <button
                                className="btn btn-danger"
                                type="button"
                                onClick={() =>
                                  handleDeleteDocument(
                                    item.id
                                  )
                                }
                              >
                                Sil
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            
              </CollapsibleSection>
            </div>
          </>
        )}


        {confirmDialog && (
          <div
            className="modal-backdrop"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) {
                closeConfirmDialog();
              }
            }}
          >
            <div
              className="modal-shell confirm-modal-shell"
              role="dialog"
              aria-modal="true"
              aria-labelledby="confirm-dialog-title"
            >
              <div className="modal-header">
                <div>
                  <span className="modal-eyebrow">Onay Gerekiyor</span>
                  <h2 id="confirm-dialog-title">{confirmDialog.title}</h2>
                </div>
                <button
                  type="button"
                  className="modal-close"
                  onClick={closeConfirmDialog}
                  aria-label="Kapat"
                >
                  ×
                </button>
              </div>

              <div className="modal-body">
                <p className="confirm-dialog-message">
                  {confirmDialog.message}
                </p>

                <div className="admin-form-actions confirm-dialog-actions">
                  <button
                    className="btn btn-light"
                    type="button"
                    onClick={closeConfirmDialog}
                  >
                    Vazgeç
                  </button>
                  <button
                    className="btn btn-danger"
                    type="button"
                    onClick={confirmDelete}
                  >
                    {confirmDialog.confirmText}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeModal && (
          <div
            className="modal-backdrop"
            onMouseDown={(event) => {
              if (
                event.target ===
                event.currentTarget
              ) {
                closeModal();
              }
            }}
          >
            <div className="modal-shell">
              <div className="modal-header">
                <div>
                  <span className="modal-eyebrow">
                    Yönetim İşlemi
                  </span>
                  <h2>
                    {activeModal === "user"
                      ? editingUserId
                        ? "Kullanıcıyı Düzenle"
                        : "Yeni Kullanıcı"
                      : activeModal === "announcement"
                      ? editingAnnouncementId
                        ? "Duyuruyu Düzenle"
                        : "Yeni Duyuru"
                      : activeModal === "event"
                      ? editingEventId
                        ? "Etkinliği Düzenle"
                        : "Yeni Etkinlik"
                      : "Dosya Yükle"}
                  </h2>
                </div>

                <button
                  type="button"
                  className="modal-close"
                  onClick={closeModal}
                  aria-label="Kapat"
                >
                  ×
                </button>
              </div>

              <div className="modal-body">
                {activeModal === "user" && (
                  <>
<form
                className="modal-form admin-form-grid"
                onSubmit={handleUserSubmit}
              >
                <input
                  placeholder="Kullanıcı adı"
                  value={userForm.username}
                  onChange={(event) =>
                    setUserForm({
                      ...userForm,
                      username:
                        event.target.value,
                    })
                  }
                  required
                />

                <input
                  type="email"
                  placeholder="E-posta"
                  value={userForm.email}
                  onChange={(event) =>
                    setUserForm({
                      ...userForm,
                      email:
                        event.target.value,
                    })
                  }
                  required
                />

                <input
                  placeholder="Ad"
                  value={userForm.first_name}
                  onChange={(event) =>
                    setUserForm({
                      ...userForm,
                      first_name:
                        event.target.value,
                    })
                  }
                  required
                />

                <input
                  placeholder="Soyad"
                  value={userForm.last_name}
                  onChange={(event) =>
                    setUserForm({
                      ...userForm,
                      last_name:
                        event.target.value,
                    })
                  }
                  required
                />

                <select
                  value={userForm.department}
                  onChange={(event) =>
                    setUserForm({
                      ...userForm,
                      department:
                        event.target.value,
                      manager_id: "",
                    })
                  }
                >
                  {DEPARTMENTS.map(
                    (department) => (
                      <option
                        key={department}
                        value={department}
                      >
                        {department ===
                        "Bilgi Teknolojileri"
                          ? "IT"
                          : department}
                      </option>
                    )
                  )}
                </select>

                <select
                  value={userForm.role}
                  onChange={(event) =>
                    setUserForm({
                      ...userForm,
                      role:
                        event.target.value,
                    })
                  }
                >
                  <option value="employee">
                    Çalışan
                  </option>
                  <option value="it_admin">
                    IT Yöneticisi
                  </option>
                  <option value="finance_admin">
                    Finans Yöneticisi
                  </option>
                  <option value="hr_admin">
                    İK Admin
                  </option>
                  <option value="admin">
                    Genel Admin
                  </option>
                </select>

                <select
                  value={userForm.manager_id}
                  onChange={(event) =>
                    setUserForm({
                      ...userForm,
                      manager_id:
                        event.target.value,
                    })
                  }
                >
                  <option value="">
                    Yönetici seçiniz
                  </option>

                  {managers
                    .filter(
                      (manager) =>
                        manager.id !==
                        editingUserId
                    )
                    .map(
                      (manager) => (
                        <option
                          key={manager.id}
                          value={manager.id}
                        >
                          {manager.first_name}{" "}
                          {manager.last_name}
                        </option>
                      )
                    )}
                </select>

                {!editingUserId ? (
                  <input
                    type="password"
                    placeholder="İlk şifre"
                    value={userForm.password}
                    onChange={(event) =>
                      setUserForm({
                        ...userForm,
                        password:
                          event.target.value,
                      })
                    }
                    minLength={6}
                    required
                  />
                ) : (
                  <input
                    type="password"
                    placeholder="Yeni şifre (opsiyonel)"
                    value={userForm.new_password}
                    onChange={(event) =>
                      setUserForm({
                        ...userForm,
                        new_password:
                          event.target.value,
                      })
                    }
                    minLength={6}
                  />
                )}

                <div className="admin-form-actions">
                  <button
                    className="btn btn-primary"
                    type="submit"
                  >
                    {editingUserId
                      ? "Kullanıcıyı Güncelle"
                      : "Kullanıcı Oluştur"}
                  </button>

                  {editingUserId && (
                    <button
                      className="btn btn-light"
                      type="button"
                      onClick={() => {
                        setEditingUserId(null);
                        setUserForm(
                          EMPTY_USER_FORM
                        );
                        closeModal();
                      }}
                    >
                      İptal
                    </button>
                  )}
                </div>
              </form>
                  </>
                )}

                {activeModal === "announcement" && (
                  <>
<form
                  className="modal-form admin-stack-form"
                  onSubmit={
                    handleAnnouncementSubmit
                  }
                >
                  <input
                    placeholder="Başlık"
                    value={
                      announcementForm.title
                    }
                    onChange={(event) =>
                      setAnnouncementForm({
                        ...announcementForm,
                        title:
                          event.target.value,
                      })
                    }
                    required
                  />

                  <textarea
                    placeholder="İçerik"
                    value={
                      announcementForm.content
                    }
                    onChange={(event) =>
                      setAnnouncementForm({
                        ...announcementForm,
                        content:
                          event.target.value,
                      })
                    }
                    required
                  />

                  <select
                    value={
                      announcementForm.department
                    }
                    onChange={(event) =>
                      setAnnouncementForm({
                        ...announcementForm,
                        department:
                          event.target.value,
                      })
                    }
                  >
                    <option value="Genel">
                      Genel
                    </option>

                    {DEPARTMENTS.map(
                      (department) => (
                        <option
                          key={department}
                          value={department}
                        >
                          {department ===
                          "Bilgi Teknolojileri"
                            ? "IT"
                            : department}
                        </option>
                      )
                    )}
                  </select>

                  <div className="admin-form-actions">
                    <button
                      className="btn btn-primary"
                      type="submit"
                    >
                      {editingAnnouncementId
                        ? "Güncelle"
                        : "Duyuru Ekle"}
                    </button>

                    {editingAnnouncementId && (
                      <button
                        className="btn btn-light"
                        type="button"
                        onClick={() => {
                          setEditingAnnouncementId(
                            null
                          );

                          setAnnouncementForm(
                            EMPTY_ANNOUNCEMENT_FORM
                          );
                          closeModal();
                        }}
                      >
                        İptal
                      </button>
                    )}
                  </div>
                </form>
                  </>
                )}

                {activeModal === "event" && (
                  <>
<form
                  className="modal-form admin-stack-form"
                  onSubmit={
                    handleEventSubmit
                  }
                >
                  <input
                    placeholder="Başlık"
                    value={eventForm.title}
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        title:
                          event.target.value,
                      })
                    }
                    required
                  />

                  <textarea
                    placeholder="Açıklama"
                    value={
                      eventForm.description
                    }
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        description:
                          event.target.value,
                      })
                    }
                    required
                  />

                  <input
                    type="datetime-local"
                    value={
                      eventForm.event_date
                    }
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        event_date:
                          event.target.value,
                      })
                    }
                    required
                  />

                  <input
                    placeholder="Konum"
                    value={eventForm.location}
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        location:
                          event.target.value,
                      })
                    }
                  />

                  <select
                    value={
                      eventForm.department
                    }
                    onChange={(event) =>
                      setEventForm({
                        ...eventForm,
                        department:
                          event.target.value,
                      })
                    }
                  >
                    <option value="Genel">
                      Genel
                    </option>

                    {DEPARTMENTS.map(
                      (department) => (
                        <option
                          key={department}
                          value={department}
                        >
                          {department ===
                          "Bilgi Teknolojileri"
                            ? "IT"
                            : department}
                        </option>
                      )
                    )}
                  </select>

                  <div className="admin-form-actions">
                    <button
                      className="btn btn-primary"
                      type="submit"
                    >
                      {editingEventId
                        ? "Güncelle"
                        : "Etkinlik Ekle"}
                    </button>

                    {editingEventId && (
                      <button
                        className="btn btn-light"
                        type="button"
                        onClick={() => {
                          setEditingEventId(
                            null
                          );

                          setEventForm(
                            EMPTY_EVENT_FORM
                          );
                          closeModal();
                        }}
                      >
                        İptal
                      </button>
                    )}
                  </div>
                </form>
                  </>
                )}

                {activeModal === "document" && (
                  <>
<form
                className="modal-form document-upload-form"
                onSubmit={
                  handleDocumentUpload
                }
              >
                <input
                  type="file"
                  onChange={(event) =>
                    setDocumentFile(
                      event.target.files?.[0] ||
                        null
                    )
                  }
                  required
                />

                <select
                  value={documentCategory}
                  onChange={(event) =>
                    setDocumentCategory(
                      event.target.value
                    )
                  }
                >
                  <option value="Genel">
                    Genel
                  </option>
                  <option value="İnsan Kaynakları">
                    İnsan Kaynakları
                  </option>
                  <option value="Finans">
                    Finans
                  </option>
                  <option value="IT">
                    IT
                  </option>
                  <option value="Prosedür">
                    Prosedür
                  </option>
                </select>

                <button
                  className="btn btn-primary"
                  type="submit"
                >
                  Dosya Yükle
                </button>
              </form>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

      </main>

    </div>
  );
}

export default Admin;

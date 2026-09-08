import ConfirmModal from "../components/ConfirmModal";
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import Sidebar from "../components/Sidebar";
import CollapsibleSection from "../components/CollapsibleSection";

function Dashboard() {
  const {
    user,
    logout,
    authLoading,
  } = useAuth();

  const [
    announcements,
    setAnnouncements,
  ] = useState([]);

  const [
    events,
    setEvents,
  ] = useState([]);

  const [
    myLeaves,
    setMyLeaves,
  ] = useState([]);

  const [
    documents,
    setDocuments,
  ] = useState([]);

  const [
    documentFile,
    setDocumentFile,
  ] = useState(null);

  const [
    documentCategory,
    setDocumentCategory,
  ] = useState("Genel");

  const [
    documentLoading,
    setDocumentLoading,
  ] = useState(false);

  const [
    dashboardLoading,
    setDashboardLoading,
  ] = useState(false);

  const [
    dashboardError,
    setDashboardError,
  ] = useState("");

  const [
    showAnnouncementForm,
    setShowAnnouncementForm,
  ] = useState(false);

  const [
    showEventForm,
    setShowEventForm,
  ] = useState(false);

  const [
    editingAnnouncement,
    setEditingAnnouncement,
  ] = useState(null);

  const [
    editingEvent,
    setEditingEvent,
  ] = useState(null);

  const [
    announcementForm,
    setAnnouncementForm,
  ] = useState({
    title: "",
    content: "",
    department: "Genel",
  });

  const [
    eventForm,
    setEventForm,
  ] = useState({
    title: "",
    description: "",
    event_date: "",
    location: "",
    department: "Genel",
  });

  const [
    formError,
    setFormError,
  ] = useState("");

  const [
    formLoading,
    setFormLoading,
  ] = useState(false);

  // =========================================================
  // YETKİ KONTROLÜ
  // =========================================================

  const role =
    String(
      user?.role || ""
    ).toLowerCase();

  const isAdmin =
    role === "admin";

  const isDepartmentManager =
    [
      "it_admin",
      "finance_admin",
      "hr_admin",
    ].includes(role);

  const canManageContent =
    isAdmin ||
    isDepartmentManager;

  const managedDepartment =
    isDepartmentManager
      ? user?.department || "Genel"
      : "Genel";

  const allowedDepartments =
    isAdmin
      ? [
          "Genel",
          "Yönetim",
          "Finans",
          "İnsan Kaynakları",
          "Bilgi Teknolojileri",
          "Satış",
          "Muhasebe",
        ]
      : [
          "Genel",
          managedDepartment,
        ];

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


  // =========================================================
  // DASHBOARD VERİLERİ
  // =========================================================

  useEffect(() => {
    const loadDashboard = async () => {
      setDashboardLoading(true);
      setDashboardError("");

      try {
        const [
          announcementsResponse,
          eventsResponse,
          leavesResponse,
          documentsResponse,
        ] = await Promise.all([
          fetch(
            "/api/announcements",
            {
              credentials: "include",
            }
          ),
          fetch(
            "/api/events",
            {
              credentials: "include",
            }
          ),
          fetch(
            "/api/leaves/my",
            {
              credentials: "include",
            }
          ),
          fetch(
            "/api/documents",
            {
              credentials: "include",
            }
          ),
        ]);

        if (
          !announcementsResponse.ok ||
          !eventsResponse.ok
        ) {
          throw new Error(
            "Dashboard verileri alınamadı."
          );
        }

        const announcementsData =
          await announcementsResponse.json();

        const eventsData =
          await eventsResponse.json();

        const leavesData =
          leavesResponse.ok
            ? await leavesResponse.json()
            : [];

        const documentsData =
          documentsResponse.ok
            ? await documentsResponse.json()
            : [];

        setAnnouncements(
          announcementsData
        );

        setEvents(eventsData);

        setMyLeaves(
          Array.isArray(leavesData)
            ? leavesData
            : []
        );

        setDocuments(
          Array.isArray(documentsData)
            ? documentsData
            : []
        );

      } catch (error) {
        console.error(
          "Dashboard veri hatası:",
          error
        );

        setDashboardError(
          "Duyuru ve etkinlik verileri alınamadı."
        );

      } finally {
        setDashboardLoading(false);
      }
    };

    loadDashboard();
  }, [authLoading, user]);

  // =========================================================
  // AUTH
  // =========================================================

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

  // =========================================================
  // DUYURU OLUŞTUR
  // =========================================================

  const handleCreateAnnouncement = async (
    event
  ) => {
    event.preventDefault();

    setFormError("");
    setFormLoading(true);

    try {
      const response = await fetch(
        "/api/announcements",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify(
            announcementForm
          ),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        setFormError(
          data.error ||
            "Duyuru oluşturulamadı."
        );
        return;
      }

      setShowAnnouncementForm(
        false
      );

      setAnnouncementForm({
        title: "",
        content: "",
        department:
          isAdmin
            ? "Genel"
            : managedDepartment,
      });

      await reloadAnnouncements();

    } catch (error) {
      console.error(
        "Duyuru oluşturma hatası:",
        error
      );

      setFormError(
        "Sunucuya bağlanırken hata oluştu."
      );

    } finally {
      setFormLoading(false);
    }
  };

  // =========================================================
  // ETKİNLİK OLUŞTUR
  // =========================================================

  const handleCreateEvent = async (
    event
  ) => {
    event.preventDefault();

    setFormError("");
    setFormLoading(true);

    try {
      const response = await fetch(
        "/api/events",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify(
            eventForm
          ),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        setFormError(
          data.error ||
            "Etkinlik oluşturulamadı."
        );
        return;
      }

      setShowEventForm(false);

      setEventForm({
        title: "",
        description: "",
        event_date: "",
        location: "",
        department:
          isAdmin
            ? "Genel"
            : managedDepartment,
      });

      await reloadEvents();

    } catch (error) {
      console.error(
        "Etkinlik oluşturma hatası:",
        error
      );

      setFormError(
        "Sunucuya bağlanırken hata oluştu."
      );

    } finally {
      setFormLoading(false);
    }
  };

  // =========================================================
  // DUYURU SİL
  // =========================================================

  const handleDeleteAnnouncement =
    async (
      announcementId
    ) => {
      const confirmed =
        await requestConfirmation({
          title: "Duyuruyu Sil",
          message: "Bu duyuruyu silmek istediğinize emin misiniz?",
          confirmText: "Sil",
          danger: true,
        });

      if (!confirmed) {
        return;
      }

      try {
        const response =
          await fetch(
            `/api/announcements/${announcementId}`,
            {
              method: "DELETE",
              credentials: "include",
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          setDashboardError(
            data.error ||
              "Duyuru silinemedi."
          );
          return;
        }

        setAnnouncements(
          (current) =>
            current.filter(
              (announcement) =>
                announcement.id !==
                announcementId
            )
        );

      } catch (error) {
        console.error(
          "Duyuru silme hatası:",
          error
        );

        setDashboardError(
          "Duyuru silinirken hata oluştu."
        );
      }
    };

  // =========================================================
  // ETKİNLİK SİL
  // =========================================================

  const handleDeleteEvent =
    async (
      eventId
    ) => {
      const confirmed =
        await requestConfirmation({
          title: "Etkinliği Sil",
          message: "Bu etkinliği silmek istediğinize emin misiniz?",
          confirmText: "Sil",
          danger: true,
        });

      if (!confirmed) {
        return;
      }

      try {
        const response =
          await fetch(
            `/api/events/${eventId}`,
            {
              method: "DELETE",
              credentials: "include",
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          setDashboardError(
            data.error ||
              "Etkinlik silinemedi."
          );
          return;
        }

        setEvents(
          (current) =>
            current.filter(
              (event) =>
                event.id !== eventId
            )
        );

      } catch (error) {
        console.error(
          "Etkinlik silme hatası:",
          error
        );

        setDashboardError(
          "Etkinlik silinirken hata oluştu."
        );
      }
    };

  // =========================================================
  // DUYURU GÜNCELLE
  // =========================================================

  const handleUpdateAnnouncement =
    async (
      event
    ) => {
      event.preventDefault();

      if (!editingAnnouncement) {
        return;
      }

      setFormError("");
      setFormLoading(true);

      try {
        const response =
          await fetch(
            `/api/announcements/${editingAnnouncement.id}`,
            {
              method: "PUT",
              headers: {
                "Content-Type":
                  "application/json",
              },
              credentials:
                "include",
              body: JSON.stringify({
                title:
                  editingAnnouncement.title,
                content:
                  editingAnnouncement.content,
                department:
                  editingAnnouncement.department,
              }),
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          setFormError(
            data.error ||
              "Duyuru güncellenemedi."
          );
          return;
        }

        setAnnouncements(
          (current) =>
            current.map(
              (announcement) =>
                announcement.id ===
                editingAnnouncement.id
                  ? {
                      ...announcement,
                      title:
                        editingAnnouncement.title,
                      content:
                        editingAnnouncement.content,
                      department:
                        editingAnnouncement.department,
                    }
                  : announcement
            )
        );

        setEditingAnnouncement(
          null
        );

      } catch (error) {
        console.error(
          "Duyuru güncelleme hatası:",
          error
        );

        setFormError(
          "Sunucuya bağlanırken hata oluştu."
        );

      } finally {
        setFormLoading(false);
      }
    };

  // =========================================================
  // ETKİNLİK GÜNCELLE
  // =========================================================

  const handleUpdateEvent =
    async (
      event
    ) => {
      event.preventDefault();

      if (!editingEvent) {
        return;
      }

      setFormError("");
      setFormLoading(true);

      try {
        const response =
          await fetch(
            `/api/events/${editingEvent.id}`,
            {
              method: "PUT",
              headers: {
                "Content-Type":
                  "application/json",
              },
              credentials:
                "include",
              body: JSON.stringify({
                title:
                  editingEvent.title,
                description:
                  editingEvent.description,
                event_date:
                  editingEvent.event_date,
                location:
                  editingEvent.location,
                department:
                  editingEvent.department,
              }),
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          setFormError(
            data.error ||
              "Etkinlik güncellenemedi."
          );
          return;
        }

        setEvents(
          (current) =>
            current.map(
              (currentEvent) =>
                currentEvent.id ===
                editingEvent.id
                  ? {
                      ...currentEvent,
                      title:
                        editingEvent.title,
                      description:
                        editingEvent.description,
                      event_date:
                        editingEvent.event_date,
                      location:
                        editingEvent.location,
                      department:
                        editingEvent.department,
                    }
                  : currentEvent
            )
        );

        setEditingEvent(
          null
        );

      } catch (error) {
        console.error(
          "Etkinlik güncelleme hatası:",
          error
        );

        setFormError(
          "Sunucuya bağlanırken hata oluştu."
        );

      } finally {
        setFormLoading(false);
      }
    };

  // =========================================================
  // DOSYA YÜKLE
  // =========================================================

  const handleDocumentUpload =
    async (event) => {
      event.preventDefault();

      if (!documentFile) {
        setFormError(
          "Dosya seçmelisiniz."
        );
        return;
      }

      setFormError("");
      setDocumentLoading(true);

      try {
        const formData =
          new FormData();

        formData.append(
          "file",
          documentFile
        );

        formData.append(
          "category",
          documentCategory
        );

        const response =
          await fetch(
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
          setFormError(
            data.error ||
              "Dosya yüklenemedi."
          );
          return;
        }

        setDocumentFile(null);
        setDocumentCategory(
          "Genel"
        );

        await reloadDocuments();

      } catch (error) {
        console.error(
          "Dosya yükleme hatası:",
          error
        );

        setFormError(
          "Dosya yüklenirken hata oluştu."
        );

      } finally {
        setDocumentLoading(false);
      }
    };


  // =========================================================
  // DOSYA SİL
  // =========================================================

  const handleDeleteDocument =
    async (documentId) => {

      const confirmed =
        await requestConfirmation({
          title: "Dosyayı Sil",
          message: "Bu dosyayı silmek istediğinize emin misiniz?",
          confirmText: "Sil",
          danger: true,
        });

      if (!confirmed) {
        return;
      }

      try {
        const response =
          await fetch(
            `/api/documents/${documentId}`,
            {
              method: "DELETE",
              credentials: "include",
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          setDashboardError(
            data.error ||
              "Dosya silinemedi."
          );
          return;
        }

        setDocuments(
          (current) =>
            current.filter(
              (document) =>
                document.id !==
                documentId
            )
        );

      } catch (error) {
        console.error(
          "Dosya silme hatası:",
          error
        );

        setDashboardError(
          "Dosya silinirken hata oluştu."
        );
      }
    };


  // =========================================================
  // VERİ YENİLEME
  // =========================================================

  const reloadAnnouncements =
    async () => {
      const response =
        await fetch(
          "/api/announcements",
          {
            credentials:
              "include",
          }
        );

      if (response.ok) {
        const data =
          await response.json();

        setAnnouncements(data);
      }
    };

  const reloadEvents =
    async () => {
      const response =
        await fetch(
          "/api/events",
          {
            credentials:
              "include",
          }
        );

      if (response.ok) {
        const data =
          await response.json();

        setEvents(data);
      }
    };

  const reloadDocuments =
    async () => {
      const response =
        await fetch(
          "/api/documents",
          {
            credentials:
              "include",
          }
        );

      if (response.ok) {
        const data =
          await response.json();

        setDocuments(
          Array.isArray(data)
            ? data
            : []
        );
      }
    };


  // =========================================================
  // FORM AÇMA
  // =========================================================

  const openAnnouncementForm =
    () => {
      setFormError("");
      setEditingAnnouncement(null);
      setEditingEvent(null);
      setShowEventForm(false);

      setAnnouncementForm({
        title: "",
        content: "",
        department:
          isAdmin
            ? "Genel"
            : managedDepartment,
      });

      setShowAnnouncementForm(true);
    };

  const openEventForm = () => {
    setFormError("");
    setEditingAnnouncement(null);
    setEditingEvent(null);
    setShowAnnouncementForm(false);

    setEventForm({
      title: "",
      description: "",
      event_date: "",
      location: "",
      department:
        isAdmin
          ? "Genel"
          : managedDepartment,
    });

    setShowEventForm(true);
  };

  const openAnnouncementEdit = (
    announcement
  ) => {
    setFormError("");
    setShowAnnouncementForm(false);
    setShowEventForm(false);
    setEditingEvent(null);

    setEditingAnnouncement({
      id: announcement.id,
      title: announcement.title,
      content:
        announcement.content,
      department:
        announcement.department,
    });
  };

  const openEventEdit = (
    event
  ) => {
    setFormError("");
    setShowAnnouncementForm(false);
    setShowEventForm(false);
    setEditingAnnouncement(null);

    setEditingEvent({
      id: event.id,
      title: event.title,
      description:
        event.description,
      event_date: event.event_date
        ? event.event_date.slice(0, 10)
        : "",
      location:
        event.location || "",
      department:
        event.department,
    });
  };

  const closeForms = () => {
    setShowAnnouncementForm(false);
    setShowEventForm(false);
    setEditingAnnouncement(null);
    setEditingEvent(null);
    setFormError("");
  };

  // =========================================================
  // DASHBOARD GÖRSEL ÖZET
  // =========================================================

  const now = new Date();

  const hour = now.getHours();

  const greeting =
    hour < 12
      ? "Günaydın"
      : hour < 18
      ? "İyi günler"
      : "İyi akşamlar";

  const todayLabel =
    now.toLocaleDateString(
      "tr-TR",
      {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      }
    );

  const pendingLeaveCount =
    myLeaves.filter(
      (leave) =>
        leave.status === "pending"
    ).length;

  const upcomingEventCount =
    events.filter(
      (event) =>
        event.event_date &&
        new Date(event.event_date) >=
          new Date(
            now.getFullYear(),
            now.getMonth(),
            now.getDate()
          )
    ).length;

  // =========================================================
  // DASHBOARD
  // =========================================================

  return (
    <div className="dashboard">

         <Sidebar />

      

      <main className="content">

        <section className="topbar dashboard-hero">

          <div className="dashboard-hero-copy">

            <span className="dashboard-date">
              {todayLabel}
            </span>

            <h1>
              {greeting},{" "}
              {user.first_name ||
                user.username}
            </h1>

            <p>
              Portalındaki güncel içerikleri ve
              süreçlerini tek bakışta takip et.
            </p>

          </div>

          <div className="dashboard-profile-summary">
            <span className="user-badge">
              {user.department}
            </span>

            <span className="dashboard-role">
              {role === "admin"
                ? "Genel Yönetici"
                : role === "it_admin"
                ? "Bilgi Teknolojileri Yöneticisi"
                : role === "finance_admin"
                ? "Finans Yöneticisi"
                : role === "hr_admin"
                ? "İnsan Kaynakları Yöneticisi"
                : "Çalışan"}
            </span>
          </div>

        </section>

        {dashboardError && (
          <div className="alert-error">
            {dashboardError}
          </div>
        )}

        {formError && (
          <div className="alert-error">
            {formError}
          </div>
        )}

        <section className="dashboard-summary-grid">

          <article className="dashboard-summary-card">
            <div className="summary-icon">
              D
            </div>

            <div>
              <span>Aktif Duyuru</span>
              <strong>
                {announcements.length}
              </strong>
            </div>
          </article>

          <article className="dashboard-summary-card">
            <div className="summary-icon">
              E
            </div>

            <div>
              <span>Yaklaşan Etkinlik</span>
              <strong>
                {upcomingEventCount}
              </strong>
            </div>
          </article>

          <article className="dashboard-summary-card">
            <div className="summary-icon">
              İ
            </div>

            <div>
              <span>Bekleyen İznim</span>
              <strong>
                {pendingLeaveCount}
              </strong>
            </div>
          </article>

        </section>

        {/* =================================================
            DUYURU EKLE
        ================================================= */}

        {showAnnouncementForm && (
          <section className="card">

            <div className="card-header">

              <div>

                <h2>
                  Yeni Duyuru
                </h2>

                <p>
                  Şirket portalına yeni bir duyuru ekle
                </p>

              </div>

              <button
                className="btn btn-light"
                type="button"
                onClick={closeForms}
              >
                Kapat
              </button>

            </div>

            <form
              className="content-editor-form"
              onSubmit={
                handleCreateAnnouncement
              }
            >

              <div className="form-group">

                <label htmlFor="announcement-title">
                  Başlık
                </label>

                <input
                  id="announcement-title"
                  type="text"
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

              </div>

              <div className="form-group">

                <label htmlFor="announcement-content">
                  İçerik
                </label>

                <textarea
                  id="announcement-content"
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

              </div>

              <div className="form-group">

                <label htmlFor="announcement-department">
                  Departman
                </label>

                <select
                  id="announcement-department"
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

                  {allowedDepartments.map(
                    (departmentOption) => (
                      <option
                        key={departmentOption}
                        value={departmentOption}
                      >
                        {departmentOption}
                      </option>
                    )
                  )}

                </select>

              </div>

              <button
                className="btn btn-primary"
                type="submit"
                disabled={formLoading}
              >
                {formLoading
                  ? "Kaydediliyor..."
                  : "Duyuruyu Oluştur"}
              </button>

            </form>

          </section>
        )}

        {/* =================================================
            ETKİNLİK EKLE
        ================================================= */}

        {showEventForm && (
          <section className="card">

            <div className="card-header">

              <div>

                <h2>
                  Yeni Etkinlik
                </h2>

                <p>
                  Şirket portalına yeni bir etkinlik ekle
                </p>

              </div>

              <button
                className="btn btn-light"
                type="button"
                onClick={closeForms}
              >
                Kapat
              </button>

            </div>

            <form
              className="content-editor-form"
              onSubmit={
                handleCreateEvent
              }
            >

              <div className="form-group">

                <label htmlFor="event-title">
                  Başlık
                </label>

                <input
                  id="event-title"
                  type="text"
                  value={
                    eventForm.title
                  }
                  onChange={(event) =>
                    setEventForm({
                      ...eventForm,
                      title:
                        event.target.value,
                    })
                  }
                  required
                />

              </div>

              <div className="form-group">

                <label htmlFor="event-description">
                  Açıklama
                </label>

                <textarea
                  id="event-description"
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

              </div>

              <div className="form-group">

                <label htmlFor="event-date">
                  Etkinlik Tarihi
                </label>

                <input
                  id="event-date"
                  type="date"
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

              </div>

              <div className="form-group">

                <label htmlFor="event-location">
                  Konum
                </label>

                <input
                  id="event-location"
                  type="text"
                  value={
                    eventForm.location
                  }
                  onChange={(event) =>
                    setEventForm({
                      ...eventForm,
                      location:
                        event.target.value,
                    })
                  }
                />

              </div>

              <div className="form-group">

                <label htmlFor="event-department">
                  Departman
                </label>

                <select
                  id="event-department"
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

                  {allowedDepartments.map(
                    (departmentOption) => (
                      <option
                        key={departmentOption}
                        value={departmentOption}
                      >
                        {departmentOption}
                      </option>
                    )
                  )}

                </select>

              </div>

              <button
                className="btn btn-primary"
                type="submit"
                disabled={formLoading}
              >
                {formLoading
                  ? "Kaydediliyor..."
                  : "Etkinliği Oluştur"}
              </button>

            </form>

          </section>
        )}

        {/* =================================================
            DUYURU DÜZENLE
        ================================================= */}

        {editingAnnouncement && (
          <section className="card">

            <div className="card-header">

              <div>

                <h2>
                  Duyuru Düzenle
                </h2>

                <p>
                  Mevcut duyuru bilgilerini güncelle
                </p>

              </div>

              <button
                className="btn btn-light"
                type="button"
                onClick={closeForms}
              >
                Kapat
              </button>

            </div>

            <form
              className="content-editor-form"
              onSubmit={
                handleUpdateAnnouncement
              }
            >

              <div className="form-group">

                <label htmlFor="edit-announcement-title">
                  Başlık
                </label>

                <input
                  id="edit-announcement-title"
                  type="text"
                  value={
                    editingAnnouncement.title
                  }
                  onChange={(event) =>
                    setEditingAnnouncement({
                      ...editingAnnouncement,
                      title:
                        event.target.value,
                    })
                  }
                  required
                />

              </div>

              <div className="form-group">

                <label htmlFor="edit-announcement-content">
                  İçerik
                </label>

                <textarea
                  id="edit-announcement-content"
                  value={
                    editingAnnouncement.content
                  }
                  onChange={(event) =>
                    setEditingAnnouncement({
                      ...editingAnnouncement,
                      content:
                        event.target.value,
                    })
                  }
                  required
                />

              </div>

              <div className="form-group">

                <label htmlFor="edit-announcement-department">
                  Departman
                </label>

                <select
                  id="edit-announcement-department"
                  value={
                    editingAnnouncement.department
                  }
                  onChange={(event) =>
                    setEditingAnnouncement({
                      ...editingAnnouncement,
                      department:
                        event.target.value,
                    })
                  }
                >

                  {allowedDepartments.map(
                    (departmentOption) => (
                      <option
                        key={departmentOption}
                        value={departmentOption}
                      >
                        {departmentOption}
                      </option>
                    )
                  )}

                </select>

              </div>

              <button
                className="btn btn-primary"
                type="submit"
                disabled={formLoading}
              >
                {formLoading
                  ? "Güncelleniyor..."
                  : "Değişiklikleri Kaydet"}
              </button>

            </form>

          </section>
        )}

        {/* =================================================
            ETKİNLİK DÜZENLE
        ================================================= */}

        {editingEvent && (
          <section className="card">

            <div className="card-header">

              <div>

                <h2>
                  Etkinlik Düzenle
                </h2>

                <p>
                  Mevcut etkinlik bilgilerini güncelle
                </p>

              </div>

              <button
                className="btn btn-light"
                type="button"
                onClick={closeForms}
              >
                Kapat
              </button>

            </div>

            <form
              className="content-editor-form"
              onSubmit={
                handleUpdateEvent
              }
            >

              <div className="form-group">

                <label htmlFor="edit-event-title">
                  Başlık
                </label>

                <input
                  id="edit-event-title"
                  type="text"
                  value={
                    editingEvent.title
                  }
                  onChange={(event) =>
                    setEditingEvent({
                      ...editingEvent,
                      title:
                        event.target.value,
                    })
                  }
                  required
                />

              </div>

              <div className="form-group">

                <label htmlFor="edit-event-description">
                  Açıklama
                </label>

                <textarea
                  id="edit-event-description"
                  value={
                    editingEvent.description
                  }
                  onChange={(event) =>
                    setEditingEvent({
                      ...editingEvent,
                      description:
                        event.target.value,
                    })
                  }
                  required
                />

              </div>

              <div className="form-group">

                <label htmlFor="edit-event-date">
                  Etkinlik Tarihi
                </label>

                <input
                  id="edit-event-date"
                  type="date"
                  value={
                    editingEvent.event_date
                  }
                  onChange={(event) =>
                    setEditingEvent({
                      ...editingEvent,
                      event_date:
                        event.target.value,
                    })
                  }
                  required
                />

              </div>

              <div className="form-group">

                <label htmlFor="edit-event-location">
                  Konum
                </label>

                <input
                  id="edit-event-location"
                  type="text"
                  value={
                    editingEvent.location
                  }
                  onChange={(event) =>
                    setEditingEvent({
                      ...editingEvent,
                      location:
                        event.target.value,
                    })
                  }
                />

              </div>

              <div className="form-group">

                <label htmlFor="edit-event-department">
                  Departman
                </label>

                <select
                  id="edit-event-department"
                  value={
                    editingEvent.department
                  }
                  onChange={(event) =>
                    setEditingEvent({
                      ...editingEvent,
                      department:
                        event.target.value,
                    })
                  }
                >

                  {allowedDepartments.map(
                    (departmentOption) => (
                      <option
                        key={departmentOption}
                        value={departmentOption}
                      >
                        {departmentOption}
                      </option>
                    )
                  )}

                </select>

              </div>

              <button
                className="btn btn-primary"
                type="submit"
                disabled={formLoading}
              >
                {formLoading
                  ? "Güncelleniyor..."
                  : "Değişiklikleri Kaydet"}
              </button>

            </form>

          </section>
        )}

        {/* =================================================
            DUYURULAR
        ================================================= */}

        <div className="grid-2">

          <section
            className="card"
            id="announcements"
          >

            <div className="card-header">

              <div>

                <h2>
                  Duyurular
                </h2>

                <p>
                  Güncel şirket duyuruları
                </p>

              </div>

              {canManageContent && (
                <button
                  className="btn btn-primary"
                  type="button"
                  onClick={
                    openAnnouncementForm
                  }
                >
                  Duyuru Ekle
                </button>
              )}

            </div>

            {dashboardLoading ? (

              <div className="empty-state">
                Duyurular yükleniyor...
              </div>

            ) : announcements.length === 0 ? (

              <div className="empty-state rich-empty-state">
                <span className="empty-state-icon">D</span>
                Güncel duyuru bulunmuyor.
              </div>

            ) : (

              announcements.map(
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

                      <span className="badge badge-gray">
                        {
                          announcement.department
                        }
                      </span>

                      {announcement.created_by && (
                        <span className="badge badge-gray">
                          {
                            announcement.created_by
                          }
                        </span>
                      )}

                      {announcement.created_at && (
                        <span className="badge badge-gray">
                          {new Date(
                            announcement.created_at
                          ).toLocaleDateString(
                            "tr-TR"
                          )}
                        </span>
                      )}

                    </div>

                    {canManageContent && (
                      <div className="action-row">

                        <button
                          className="btn btn-light"
                          type="button"
                          onClick={() =>
                            openAnnouncementEdit(
                              announcement
                            )
                          }
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
                    )}

                  </div>

                )
              )

            )}

          </section>

          {/* =================================================
              ETKİNLİKLER
          ================================================= */}

          <section
            className="card"
            id="events"
          >

            <div className="card-header">

              <div>

                <h2>
                  Etkinlikler
                </h2>

                <p>
                  Yaklaşan şirket etkinlikleri
                </p>

              </div>

              {canManageContent && (
                <button
                  className="btn btn-primary"
                  type="button"
                  onClick={
                    openEventForm
                  }
                >
                  Etkinlik Ekle
                </button>
              )}

            </div>

            {dashboardLoading ? (

              <div className="empty-state">
                Etkinlikler yükleniyor...
              </div>

            ) : events.length === 0 ? (

              <div className="empty-state rich-empty-state">
                <span className="empty-state-icon">E</span>
                Yaklaşan etkinlik bulunmuyor.
              </div>

            ) : (

              events.map(
                (event) => (

                  <div
                    className="content-item"
                    key={event.id}
                  >

                    <h3>
                      {event.title}
                    </h3>

                    <p>
                      {event.description}
                    </p>

                    <div className="item-meta">

                      {event.event_date && (
                        <span className="badge badge-gray">
                          {new Date(
                            event.event_date
                          ).toLocaleDateString(
                            "tr-TR"
                          )}
                        </span>
                      )}

                      {event.location && (
                        <span className="badge badge-gray">
                          {event.location}
                        </span>
                      )}

                      <span className="badge badge-gray">
                        {event.department}
                      </span>

                    </div>

                    {canManageContent && (
                      <div className="action-row">

                        <button
                          className="btn btn-light"
                          type="button"
                          onClick={() =>
                            openEventEdit(
                              event
                            )
                          }
                        >
                          Düzenle
                        </button>

                        <button
                          className="btn btn-danger"
                          type="button"
                          onClick={() =>
                            handleDeleteEvent(
                              event.id
                            )
                          }
                        >
                          Sil
                        </button>

                      </div>
                    )}

                  </div>

                )
              )

            )}

          </section>

        </div>


        {/* =================================================
            DOSYALAR
        ================================================= */}

        <section
          className="card"
          id="documents"
          style={{ marginTop: "24px" }}
        >
          <div className="card-header">

            <div>
              <h2>
                Dosyalar
              </h2>

              <p>
                Şirket içi paylaşılan dosyalar
              </p>
            </div>

          </div>


          {canManageContent && (
            <form
              className="document-upload-form"
              onSubmit={
                handleDocumentUpload
              }
            >

              <div className="form-group">

                <label>
                  Dosya
                </label>

                <input
                  type="file"
                  onChange={(event) =>
                    setDocumentFile(
                      event.target
                        .files?.[0] ||
                        null
                    )
                  }
                  required
                />

              </div>


              <div className="form-group">

                <label>
                  Kategori
                </label>

                <select
                  value={
                    documentCategory
                  }
                  onChange={(event) =>
                    setDocumentCategory(
                      event.target.value
                    )
                  }
                >

                  <option value="Genel">
                    Genel
                  </option>

                  {isDepartmentManager && (
                    <option
                      value={
                        managedDepartment
                      }
                    >
                      {
                        managedDepartment
                      }
                    </option>
                  )}

                  {isAdmin && (
                    <>
                      <option value="Bilgi Teknolojileri">
                        Bilgi Teknolojileri
                      </option>

                      <option value="Finans">
                        Finans
                      </option>

                      <option value="İnsan Kaynakları">
                        İnsan Kaynakları
                      </option>
                    </>
                  )}

                </select>

              </div>


              <button
                className="btn btn-primary"
                type="submit"
                disabled={
                  documentLoading
                }
              >
                {documentLoading
                  ? "Yükleniyor..."
                  : "Dosya Yükle"}
              </button>

            </form>
          )}


          {documents.length === 0 ? (

            <div className="empty-state">
              Henüz dosya bulunmuyor.
            </div>

          ) : (

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
                    (document) => (

                      <tr
                        key={
                          document.id
                        }
                      >

                        <td>
                          {
                            document.file_name
                          }
                        </td>

                        <td>
                          {
                            document.category
                          }
                        </td>

                        <td>
                          {
                            document.uploaded_by ||
                            "-"
                          }
                        </td>

                        <td>
                          {document.uploaded_at
                            ? new Date(
                                document.uploaded_at
                              ).toLocaleDateString(
                                "tr-TR"
                              )
                            : "-"}
                        </td>

                        <td>

                          <div className="action-row">

                            <a
                              className="btn btn-light"
                              href={
                                `/api/documents/${document.id}/download`
                              }
                            >
                              İndir
                            </a>

                            {canManageContent && (
                              <button
                                className="btn btn-danger"
                                type="button"
                                onClick={() =>
                                  handleDeleteDocument(
                                    document.id
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

export default Dashboard;
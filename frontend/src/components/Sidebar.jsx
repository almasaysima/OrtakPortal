import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import ortakPortalMark from "../assets/ortakportal-mark.png";

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const { user, logout } = useAuth();

  const [showModal, setShowModal] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const role = String(user?.role || "").toLowerCase();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const go = (path) => {
    navigate(path);
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError("");
    setMsg("");

    if (!newPassword || newPassword.length < 6) {
      setError("Yeni parola en az 6 karakter olmalıdır.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Parolalar birbiriyle uyuşmuyor.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: newPassword }),
      });

      const data = await res.json();
      if (data.success) {
        setMsg(data.message || "Parolanız başarıyla güncellendi!");
        setNewPassword("");
        setConfirmPassword("");
        setTimeout(() => {
          setShowModal(false);
          setMsg("");
        }, 2500);
      } else {
        setError(data.error || "Parola güncellenirken hata oluştu.");
      }
    } catch (err) {
      setError("Sunucuya bağlanılamadı.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-main">
          <img
            className="sidebar-brand-logo"
            src={ortakPortalMark}
            alt=""
          />
          <h2>OrtakPortal</h2>
        </div>

        <span>
          {role === "admin"
            ? "Yönetim"
            : role === "hr_admin"
            ? "İnsan Kaynakları"
            : "Çalışan Portalı"}
        </span>
      </div>

      <nav className="sidebar-nav">
        {role === "admin" ? (
          <>
            <button
              className={`sidebar-link ${
                location.pathname === "/admin" ? "active" : ""
              }`}
              type="button"
              onClick={() => go("/admin")}
            >
              Admin Paneli
            </button>

            <button
              className="sidebar-link"
              type="button"
              onClick={() => go("/")}
            >
              Portal Görünümü
            </button>

            <button
              className="sidebar-link"
              type="button"
              onClick={() => go("/hr")}
            >
              İnsan Kaynakları
            </button>
          </>
        ) : (
          <>
            <button
              className={`sidebar-link ${
                location.pathname === "/" ? "active" : ""
              }`}
              type="button"
              onClick={() => go("/")}
            >
              Ana Sayfa
            </button>

            <button
              className={`sidebar-link ${
                location.pathname === "/hr" ? "active" : ""
              }`}
              type="button"
              onClick={() => go("/hr")}
            >
              İnsan Kaynakları
            </button>

            <button
              className={`sidebar-link ${
                location.pathname === "/leaves" ? "active" : ""
              }`}
              type="button"
              onClick={() => go("/leaves")}
            >
              İzinler
            </button>
          </>
        )}
      </nav>

      <div className="sidebar-bottom">
        <button
          className="sidebar-link"
          type="button"
          onClick={() => {
            setShowModal(true);
            setError("");
            setMsg("");
          }}
          style={{ color: "#b91c1c", fontWeight: "600" }}
        >
          🔑 Şifre Değiştir
        </button>

        <button
          className="sidebar-link"
          type="button"
          onClick={handleLogout}
        >
          Çıkış Yap
        </button>
      </div>

      {showModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 9999,
          }}
        >
          <div
            style={{
              backgroundColor: "#fff",
              padding: "24px",
              borderRadius: "12px",
              width: "360px",
              boxShadow: "0 8px 30px rgba(0,0,0,0.2)",
              color: "#1e293b",
            }}
          >
            <h3 style={{ margin: "0 0 16px 0", fontSize: "18px", color: "#b91c1c" }}>
              🔑 Parola Değiştir
            </h3>

            {error && (
              <div
                style={{
                  padding: "8px 12px",
                  backgroundColor: "#fee2e2",
                  color: "#991b1b",
                  borderRadius: "6px",
                  fontSize: "13px",
                  marginBottom: "12px",
                }}
              >
                {error}
              </div>
            )}

            {msg && (
              <div
                style={{
                  padding: "8px 12px",
                  backgroundColor: "#dcfce7",
                  color: "#166534",
                  borderRadius: "6px",
                  fontSize: "13px",
                  marginBottom: "12px",
                }}
              >
                {msg}
              </div>
            )}

            <form onSubmit={handlePasswordChange}>
              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "4px" }}>
                  Yeni Parola
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="En az 6 karakter"
                  required
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    border: "1px solid #cbd5e1",
                    borderRadius: "6px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "500", marginBottom: "4px" }}>
                  Yeni Parola (Tekrar)
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Yeni parolayı tekrar girin"
                  required
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    border: "1px solid #cbd5e1",
                    borderRadius: "6px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  style={{
                    padding: "8px 16px",
                    backgroundColor: "#f1f5f9",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontSize: "13px",
                  }}
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    padding: "8px 16px",
                    backgroundColor: "#b91c1c",
                    color: "#fff",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontWeight: "500",
                    fontSize: "13px",
                  }}
                >
                  {loading ? "Güncelleniyor..." : "Güncelle"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
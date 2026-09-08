import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import ortakPortalMark from "../assets/ortakportal-mark.png";


function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    user,
    logout,
  } = useAuth();

  const role =
    String(user?.role || "").toLowerCase();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const go = (
    path
  ) => {
    navigate(path);
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

          <h2>
            OrtakPortal
          </h2>
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
                location.pathname ===
                "/admin"
                  ? "active"
                  : ""
              }`}
              type="button"
              onClick={() =>
                go("/admin")
              }
            >
              Admin Paneli
            </button>

            <button
              className="sidebar-link"
              type="button"
              onClick={() =>
                go("/")
              }
            >
              Portal Görünümü
            </button>

            <button
              className="sidebar-link"
              type="button"
              onClick={() =>
                go("/hr")
              }
            >
              İnsan Kaynakları
            </button>
          </>
        ) : (
          <>
            <button
              className={`sidebar-link ${
                location.pathname === "/"
                  ? "active"
                  : ""
              }`}
              type="button"
              onClick={() =>
                go("/")
              }
            >
              Ana Sayfa
            </button>

            <button
              className={`sidebar-link ${
                location.pathname === "/hr"
                  ? "active"
                  : ""
              }`}
              type="button"
              onClick={() =>
                go("/hr")
              }
            >
              İnsan Kaynakları
            </button>

            <button
              className={`sidebar-link ${
                location.pathname ===
                "/leaves"
                  ? "active"
                  : ""
              }`}
              type="button"
              onClick={() =>
                go("/leaves")
              }
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
          onClick={
            handleLogout
          }
        >
          Çıkış Yap
        </button>
      </div>

    </aside>
  );
}

export default Sidebar;

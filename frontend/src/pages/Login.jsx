import { useEffect, useState } from "react";
import { Navigate, useNavigate, Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import Toast from "../components/Toast";
import ortakPortalMark from "../assets/ortakportal-mark.png";

function Login() {
  const {
    user,
    login,
    authLoading,
  } = useAuth();

  const navigate = useNavigate();

  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  if (user) {
    const role =
      String(user.role || "").toLowerCase();

    if (role === "admin") {
      return (
        <Navigate
          to="/admin"
          replace
        />
      );
    }

    if (role === "hr_admin") {
      return (
        <Navigate
          to="/hr"
          replace
        />
      );
    }

    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    setError("");

    if (
      !username.trim() ||
      !password
    ) {
      setError(
        "Kullanıcı adı ve parola zorunludur."
      );
      return;
    }

    const result = await login(
      username.trim(),
      password
    );

    if (!result.success) {
      setError(result.error);
      return;
    }

    setPassword("");

    const role =
      String(result.user?.role || "").toLowerCase();

    if (role === "admin") {
      navigate("/admin");
      return;
    }

    if (role === "hr_admin") {
      navigate("/hr");
      return;
    }

    navigate("/");
  };

  return (
    <div className="login-page">

      <div className="login-card">

        <div className="brand">

          <div className="brand-mark brand-mark-image">
            <img
              src={ortakPortalMark}
              alt="OrtakPortal"
            />
          </div>

          <h1>
            OrtakPortal
          </h1>

          <p>
            Çalışan portalına hoş geldiniz
          </p>

        </div>

        {error && <Toast message={error} type="error" />}

        <form
          onSubmit={handleSubmit}
        >

          <div className="form-group">

            <label htmlFor="username">
              Kullanıcı Adı
            </label>

            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) =>
                setUsername(
                  event.target.value
                )
              }
              autoComplete="username"
              disabled={authLoading}
              required
            />

          </div>

          <div className="form-group">

            <label htmlFor="password">
              Parola
            </label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value
                )
              }
              autoComplete="current-password"
              disabled={authLoading}
              required
            />

          </div>

          <button
            type="submit"
            disabled={authLoading}
          >
            {authLoading
              ? "Giriş yapılıyor..."
              : "Giriş Yap"}
          </button>

        </form>

        <div className="auth-link-row">
          <div style={{ textAlign: "center", marginTop: "12px", marginBottom: "12px" }}>
            <Link
              to="/forgot-password"
              style={{
                color: "#b91c1c",
                fontSize: "14px",
                textDecoration: "none",
                fontWeight: "500"
              }}
            >
              Şifremi Unuttum
            </Link>
          </div>

          <p className="login-password-notice">
            Parolanız şirket hesabınız üzerinden
            yönetilmektedir. Parola işlemleri için
            Bilgi Teknolojileri birimiyle iletişime
            geçiniz.
          </p>
        </div>

      </div>

    </div>
  );
}

export default Login;
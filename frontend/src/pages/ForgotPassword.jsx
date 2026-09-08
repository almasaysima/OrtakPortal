import { useState } from "react";
import { Link } from "react-router-dom";
import Toast from "../components/Toast";
import ortakPortalMark from "../assets/ortakportal-mark.png";


function ForgotPassword() {
  const [email, setEmail] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        "/api/password-reset/request",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            email,
          }),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.error ||
          "İşlem gerçekleştirilemedi."
        );
      }

      setMessage(
        data.message
      );

    } catch (requestError) {
      setError(
        requestError.message
      );

    } finally {
      setLoading(false);
    }
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
            Şifremi Unuttum
          </h1>

          <p>
            E-posta adresinizi girin.
          </p>

        </div>

        {error && <Toast message={error} type="error" />}

        {message && <Toast message={message} type="success" />}

        <form
          onSubmit={handleSubmit}
        >

          <div className="form-group">

            <label htmlFor="email">
              E-posta
            </label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value
                )
              }
              autoComplete="email"
              required
            />

          </div>

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Gönderiliyor..."
              : "Şifre Sıfırlama Bağlantısı Gönder"}
          </button>

        </form>

        <div className="auth-link-row">
          <Link to="/login">
            Giriş ekranına dön
          </Link>
        </div>

      </div>

    </div>
  );
}

export default ForgotPassword;
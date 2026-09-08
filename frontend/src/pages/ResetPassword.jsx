import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import Toast from "../components/Toast";
import ortakPortalMark from "../assets/ortakportal-mark.png";


function ResetPassword() {
  const {
    token,
  } = useParams();

  const navigate =
    useNavigate();

  const [password, setPassword] =
    useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [loading, setLoading] =
    useState(false);

  const [validating, setValidating] =
    useState(true);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");

  useEffect(() => {
    const validateToken =
      async () => {
        try {
          const response =
            await fetch(
              `/api/password-reset/validate/${token}`
            );

          const data =
            await response.json();

          if (!response.ok) {
            throw new Error(
              data.error ||
              "Geçersiz bağlantı."
            );
          }

        } catch (
          validateError
        ) {
          setError(
            validateError.message
          );

        } finally {
          setValidating(false);
        }
      };

    validateToken();
  }, [token]);

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    setError("");
    setMessage("");

    if (
      password !==
      confirmPassword
    ) {
      setError(
        "Girdiğiniz şifreler aynı değil."
      );
      return;
    }

    if (
      password.length < 6
    ) {
      setError(
        "Şifre en az 6 karakter olmalıdır."
      );
      return;
    }

    setLoading(true);

    try {
      const response =
        await fetch(
          `/api/password-reset/reset/${token}`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              password,
              confirm_password:
                confirmPassword,
            }),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.error ||
          "Şifre güncellenemedi."
        );
      }

      setMessage(
        data.message
      );

      setTimeout(() => {
        navigate("/login");
      }, 1200);

    } catch (requestError) {
      setError(
        requestError.message
      );

    } finally {
      setLoading(false);
    }
  };

  if (validating) {
    return (
      <div className="login-page">
        <div className="login-card">
          Bağlantı kontrol ediliyor...
        </div>
      </div>
    );
  }

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
            Yeni Şifre
          </h1>

          <p>
            Hesabınız için yeni şifrenizi belirleyin.
          </p>

        </div>

        {error && <Toast message={error} type="error" />}

        {message && <Toast message={message} type="success" />}

        {!error && (
          <form
            onSubmit={handleSubmit}
          >

            <div className="form-group">

              <label htmlFor="password">
                Yeni Şifre
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
                minLength={6}
                required
              />

            </div>

            <div className="form-group">

              <label htmlFor="confirm_password">
                Yeni Şifre Tekrar
              </label>

              <input
                id="confirm_password"
                type="password"
                value={
                  confirmPassword
                }
                onChange={(event) =>
                  setConfirmPassword(
                    event.target.value
                  )
                }
                minLength={6}
                required
              />

            </div>

            <button
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Güncelleniyor..."
                : "Şifreyi Değiştir"}
            </button>

          </form>
        )}

        <div className="auth-link-row">
          <Link to="/login">
            Giriş ekranına dön
          </Link>
        </div>

      </div>

    </div>
  );
}

export default ResetPassword;
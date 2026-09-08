import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

const AuthContext = createContext(null);

export function AuthProvider({
  children,
}) {
  const [user, setUser] = useState(null);

  const [authLoading, setAuthLoading] =
    useState(true);

  // =========================================================
  // MEVCUT OTURUMU KONTROL ET
  // =========================================================

  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const response =
          await fetch(
            "/api/auth/me",
            {
              credentials: "include",
            }
          );

        if (!response.ok) {
          setUser(null);
          return;
        }

        const data =
          await response.json();

        if (
          data.success &&
          data.user
        ) {
          setUser(data.user);
        } else {
          setUser(null);
        }

      } catch (error) {
        console.error(
          "Oturum kontrolü hatası:",
          error
        );

        setUser(null);

      } finally {
        setAuthLoading(false);
      }
    };

    loadCurrentUser();
  }, []);

  // =========================================================
  // LOGIN
  // =========================================================

  const login = async (
    username,
    password
  ) => {
    setAuthLoading(true);

    try {
      const response =
        await fetch(
          "/api/auth/login",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            credentials: "include",
            body: JSON.stringify({
              username,
              password,
            }),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        return {
          success: false,
          error:
            data.error ||
            "Giriş işlemi başarısız oldu.",
        };
      }

      setUser(data.user);

      return {
        success: true,
        user: data.user,
      };

    } catch (error) {
      console.error(
        "Authentication hatası:",
        error
      );

      return {
        success: false,
        error:
          "Sunucuya bağlanırken bir hata oluştu.",
      };

    } finally {
      setAuthLoading(false);
    }
  };

  // =========================================================
  // LOGOUT
  // =========================================================

  const logout = async () => {
    try {
      await fetch(
        "/api/auth/logout",
        {
          method: "POST",
          credentials: "include",
        }
      );
    } catch (error) {
      console.error(
        "Logout hatası:",
        error
      );
    }

    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        login,
        logout,
        authLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(
    AuthContext
  );
}
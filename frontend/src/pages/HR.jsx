import { useState } from "react";
import { Navigate } from "react-router-dom";

import Sidebar from "../components/Sidebar";
import Toast from "../components/Toast";
import { useAuth } from "../context/AuthContext";

function HR() {
  const { user } = useAuth();

  const [search, setSearch] = useState("");
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  const handleSearch = async (event) => {
    event.preventDefault();

    const query = search.trim();

    if (!query) {
      setEmployees([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `/api/employees/search?q=${encodeURIComponent(query)}`,
        {
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(
          data.error ||
            "Çalışanlar getirilemedi."
        );
        setEmployees([]);
        return;
      }

      setEmployees(
        data.employees || data
      );

    } catch (error) {
      console.error(
        "Employee search hatası:",
        error
      );

      setError(
        "Sunucuya bağlanırken hata oluştu."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">

      <Sidebar />

      <main className="content">

        <section className="topbar">

          <div>

            <h1>
              İnsan Kaynakları
            </h1>

            <p>
              Çalışanları ve organizasyon yapısını
              buradan görüntüleyebilirsin.
            </p>

          </div>

        </section>

        <section className="card">

          <div className="card-header">

            <div>

              <h2>
                Çalışan Arama
              </h2>

              <p>
                Ad, soyad veya kullanıcı adına göre ara.
              </p>

            </div>

          </div>

          <form
            className="employee-search-form"
            onSubmit={handleSearch}
          >

            <input
              type="text"
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value
                )
              }
              placeholder="Çalışan ara..."
            />

            <button
              className="btn btn-primary"
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Aranıyor..."
                : "Ara"}
            </button>

          </form>

          {error && (
            <div className="alert-error">
              {error}
            </div>
          )}

          {employees.length === 0 && !loading && !error && (
            <div className="empty-state">
              Arama yapmak için bir çalışan adı gir.
            </div>
          )}

          {employees.length > 0 && (
            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>
                    <th>Çalışan</th>
                    <th>Kullanıcı Adı</th>
                    <th>Departman</th>
                    <th>Yönetici</th>
                  </tr>

                </thead>

                <tbody>

                  {employees.map(
                    (employee) => (
                      <tr
                        key={employee.id}
                      >

                        <td>
                          {employee.first_name}{" "}
                          {employee.last_name}
                        </td>

                        <td>
                          {employee.username}
                        </td>

                        <td>
                          {
                            employee.department
                          }
                        </td>

                        <td>
                          {employee.manager
                            ? `${employee.manager.first_name} ${employee.manager.last_name}`
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

      </main>

    </div>
  );
}

export default HR;
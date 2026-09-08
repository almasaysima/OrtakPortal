import {
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import HR from "./pages/HR";
import Leaves from "./pages/Leaves";
import Admin from "./pages/Admin";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";

import "./App.css";


function AnimatedPage({ children }) {
  return (
    <div className="route-page">
      {children}
    </div>
  );
}


function App() {
  const location = useLocation();

  return (
    <div
      className="route-transition"
      key={location.pathname}
    >
      <Routes location={location}>
        <Route
          path="/login"
          element={
            <AnimatedPage>
              <Login />
            </AnimatedPage>
          }
        />

        <Route
          path="/forgot-password"
          element={
            <AnimatedPage>
              <ForgotPassword />
            </AnimatedPage>
          }
        />

        <Route
          path="/reset-password/:token"
          element={
            <AnimatedPage>
              <ResetPassword />
            </AnimatedPage>
          }
        />

        <Route
          path="/"
          element={
            <AnimatedPage>
              <Dashboard />
            </AnimatedPage>
          }
        />

        <Route
          path="/hr"
          element={
            <AnimatedPage>
              <HR />
            </AnimatedPage>
          }
        />

        <Route
          path="/leaves"
          element={
            <AnimatedPage>
              <Leaves />
            </AnimatedPage>
          }
        />

        <Route
          path="/admin"
          element={
            <AnimatedPage>
              <Admin />
            </AnimatedPage>
          }
        />

        <Route
          path="*"
          element={
            <Navigate
              to="/"
              replace
            />
          }
        />
      </Routes>
    </div>
  );
}

export default App;

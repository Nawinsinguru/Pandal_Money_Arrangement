import { useState } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Dashboard from "./Dashboard";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
  UserRound,
} from "lucide-react";

import api from "./api";

function AuthLayout({ children, mode, setMode }) {
  return (
    <div className="auth-page">
      <div className="auth-orb auth-orb-one" />
      <div className="auth-orb auth-orb-two" />
      <div className="auth-grid" />

      <div className="auth-shell">
        {/* LEFT SIDE */}
        <motion.div
          className="auth-brand"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="brand-badge">
            <Sparkles size={16} />
            Festival Finance
          </div>

          <h1>
            Every rupee.
            <br />
            <span>Accounted for.</span>
          </h1>

          <p>
            A simple and transparent way for your committee to manage
            contributions, expenses and the remaining pandal budget.
          </p>

          <div className="trust-row">
            <div>
              <ShieldCheck size={20} />
              <span>Secure</span>
            </div>

            <div>
              <ShieldCheck size={20} />
              <span>Transparent</span>
            </div>

            <div>
              <ShieldCheck size={20} />
              <span>Shared</span>
            </div>
          </div>
        </motion.div>

        {/* RIGHT SIDE */}
        <motion.div
          className="auth-card"
          initial={{ opacity: 0, y: 30, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          {children}

          <div className="auth-switch">
            {mode === "login" ? (
              <>
                Don't have an account?
                <button onClick={() => setMode("register")}>
                  Create account
                  <ArrowRight size={15} />
                </button>
              </>
            ) : (
              <>
                Already have an account?
                <button onClick={() => setMode("login")}>
                  Sign in
                  <ArrowRight size={15} />
                </button>
              </>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function LoginForm({ switchToRegister }) {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", form);

      localStorage.setItem("access_token", response.data.access_token);

      localStorage.setItem("user_id", response.data.user_id);

      localStorage.setItem("user_email", response.data.email);

      navigate("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to sign in. Please check your credentials.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="auth-card-header">
        <div className="mini-logo">
          <Sparkles size={19} />
        </div>

        <div>
          <h2>Welcome back</h2>
          <p>Sign in to manage your pandal budget.</p>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="auth-form">
        <label>Email address</label>

        <div className="input-wrap">
          <Mail size={18} />
          <input
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
            required
          />
        </div>

        <label>Password</label>

        <div className="input-wrap">
          <LockKeyhole size={18} />

          <input
            type={showPassword ? "text" : "password"}
            placeholder="Enter your password"
            value={form.password}
            onChange={(e) =>
              setForm({
                ...form,
                password: e.target.value,
              })
            }
            required
          />

          <button
            type="button"
            className="input-action"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>

        <button className="primary-button" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}

          {!loading && <ArrowRight size={18} />}
        </button>
      </form>
    </>
  );
}

function RegisterForm({ switchToLogin }) {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/register", form);

      if (response.data.access_token) {
        localStorage.setItem("access_token", response.data.access_token);

        localStorage.setItem("user_id", response.data.user_id);

        localStorage.setItem("user_email", response.data.email);

        navigate("/dashboard");
      } else {
        switchToLogin();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to create your account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="auth-card-header">
        <div className="mini-logo">
          <UserRound size={19} />
        </div>

        <div>
          <h2>Create account</h2>
          <p>Set up your committee account.</p>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="auth-form">
        <label>Full name</label>

        <div className="input-wrap">
          <UserRound size={18} />

          <input
            type="text"
            placeholder="Your full name"
            value={form.full_name}
            onChange={(e) =>
              setForm({
                ...form,
                full_name: e.target.value,
              })
            }
            required
          />
        </div>

        <label>Email address</label>

        <div className="input-wrap">
          <Mail size={18} />

          <input
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
            required
          />
        </div>

        <label>Password</label>

        <div className="input-wrap">
          <LockKeyhole size={18} />

          <input
            type={showPassword ? "text" : "password"}
            placeholder="Minimum 8 characters"
            value={form.password}
            onChange={(e) =>
              setForm({
                ...form,
                password: e.target.value,
              })
            }
            minLength={8}
            required
          />

          <button
            type="button"
            className="input-action"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>

        <button className="primary-button" disabled={loading}>
          {loading ? "Creating account..." : "Create account"}

          {!loading && <ArrowRight size={18} />}
        </button>
      </form>
    </>
  );
}

function AuthPage() {
  const [mode, setMode] = useState("login");

  return (
    <AuthLayout mode={mode} setMode={setMode}>
      {mode === "login" ? (
        <LoginForm switchToRegister={() => setMode("register")} />
      ) : (
        <RegisterForm switchToLogin={() => setMode("login")} />
      )}
    </AuthLayout>
  );
}

function DashboardPlaceholder() {
  const navigate = useNavigate();

  const logout = () => {
    localStorage.clear();
    navigate("/login");
  };

  return (
    <div className="placeholder-page">
      <div>
        <Sparkles size={32} />
        <h1>Dashboard</h1>
        <p>Your dashboard is coming together.</p>

        <button className="primary-button" onClick={logout}>
          Logout
        </button>
      </div>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />

      <Route path="/dashboard" element={<Dashboard />} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;

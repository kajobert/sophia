
import React, { useState, useEffect } from "react";
import Chat from "./components/Chat";
import Login from "./components/Login";
import Upload from "./components/Upload";
import Files from "./components/Files";
import Profile from "./components/Profile";
import Notifications from "./components/Notifications";
import Settings from "./components/Settings";
import Helpdesk from "./components/Helpdesk";
import Language from "./components/Language";
import RoleManager from "./components/RoleManager";
import UserInfo from "./components/UserInfo";

const MENU = [
  { key: "chat", label: "Chat", component: <Chat /> },
  { key: "upload", label: "Nahrávání", component: <Upload /> },
  { key: "files", label: "Soubory", component: <Files /> },
  { key: "profile", label: "Profil", component: <Profile /> },
  { key: "notifications", label: "Notifikace", component: <Notifications /> },
  { key: "settings", label: "Nastavení", component: <Settings /> },
  { key: "helpdesk", label: "Helpdesk", component: <Helpdesk /> },
  { key: "language", label: "Jazyk", component: <Language /> },
  { key: "roles", label: "Role", component: <RoleManager /> },
];

function App() {
  const [user, setUser] = useState(null);
  const [active, setActive] = useState("chat");
  const [loading, setLoading] = useState(true);
  const [loginSkipped, setLoginSkipped] = useState(false);

  useEffect(() => {
    if (loginSkipped) {
      setLoading(false);
      setUser(null);
      return;
    }
    fetch("/api/me", { credentials: "include" })
      .then((res) => {
        if (res.status === 200) return res.json();
        throw new Error("not-auth");
      })
      .then((data) => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        setUser(null);
        setLoading(false);
      });
  }, [loginSkipped]);

  const handleLogout = () => {
    fetch("/api/logout", { method: "POST", credentials: "include" })
      .then(() => {
        setUser(null);
        setLoginSkipped(false);
      });
  };

  if (loading) {
    return <div style={{ fontFamily: "sans-serif", maxWidth: 600, margin: "0 auto", textAlign: "center", marginTop: 80 }}>Načítání...</div>;
  }

  if (!user && !loginSkipped) {
    return (
      <div style={{ fontFamily: "sans-serif", maxWidth: 600, margin: "0 auto" }}>
        <h1>Sophia Web UI</h1>
        <div style={{ border: "1px solid #ccc", borderRadius: 4, padding: 16, minHeight: 120 }}>
          <Login onSkip={() => setLoginSkipped(true)} onLogin={() => setUser({ name: "Host" })} />
          <div style={{ marginTop: 16, textAlign: "center" }}>
            <button
              onClick={() => setLoginSkipped(true)}
              style={{ padding: "8px 16px", background: "#eee", color: "#222", border: "none", borderRadius: 4, cursor: "pointer" }}
            >
              Přeskočit přihlášení
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 600, margin: "0 auto" }}>
      <h1>Sophia Web UI</h1>
      <UserInfo user={user} onLogout={handleLogout} />
      <nav style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
        {MENU.map((item) => (
          <button
            key={item.key}
            onClick={() => setActive(item.key)}
            style={{
              padding: "8px 16px",
              background: active === item.key ? "#1976d2" : "#eee",
              color: active === item.key ? "#fff" : "#222",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div style={{ border: "1px solid #ccc", borderRadius: 4, padding: 16, minHeight: 120 }}>
        {MENU.find((item) => item.key === active)?.component}
      </div>
    </div>
  );
}

export default App;


import React from "react";

export default function Login({ onSkip, onLogin }) {
  const handleLogin = () => {
    if (onLogin) onLogin();
    window.location.href = "/api/login";
  };
  return (
    <div style={{ textAlign: "center" }}>
      <h2>Přihlášení</h2>
      <button onClick={handleLogin} style={{ padding: "10px 24px", fontSize: 18, background: "#1976d2", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
        Přihlásit se přes Google
      </button>
      <div style={{ marginTop: 16, color: "#888" }}>
        (Budete přesměrováni na Google OAuth2)
      </div>
    </div>
  );
}

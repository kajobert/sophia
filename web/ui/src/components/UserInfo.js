import React from "react";

export default function UserInfo({ user, onLogout }) {
  if (!user) return null;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
      {user.avatar && (
        <img src={user.avatar} alt="avatar" style={{ width: 32, height: 32, borderRadius: "50%" }} />
      )}
      <span>{user.name || user.email}</span>
      <button onClick={onLogout} style={{ padding: "4px 12px", background: "#eee", color: "#222", border: "none", borderRadius: 4, cursor: "pointer" }}>
        Odhlásit se
      </button>
    </div>
  );
}

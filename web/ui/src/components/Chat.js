

import React, { useState } from "react";

export default function Chat() {
  const [messages, setMessages] = useState([
    { from: "sophia", text: "Vítej! Zeptej se na cokoliv." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { from: "user", text: input }]);
    setLoading(true);
    setError("");
    const userMsg = input;
    setInput("");
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg })
      });
      if (!res.ok) throw new Error("Chyba komunikace s API");
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        { from: "sophia", text: data.response || "(prázdná odpověď)" }
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { from: "sophia", text: "[Chyba backendu: " + err.message + "]" }
      ]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ minHeight: 120, marginBottom: 12 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ textAlign: msg.from === "user" ? "right" : "left", margin: "4px 0" }}>
            <span style={{ fontWeight: msg.from === "sophia" ? "bold" : "normal" }}>
              {msg.from === "user" ? "Vy: " : "Sophia: "}
            </span>
            {msg.text}
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Napište zprávu..."
          style={{ flex: 1, padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          disabled={loading}
        />
        <button type="submit" style={{ padding: "8px 18px", background: "#1976d2", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }} disabled={loading}>
          {loading ? "..." : "Odeslat"}
        </button>
      </form>
      {error && <div style={{ color: "#c00", marginTop: 8 }}>{error}</div>}
    </div>
  );
}

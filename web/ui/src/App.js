
import React, { useState } from "react";
import TaskRunner from "./components/TaskRunner";

function App() {
  const [currentUser, setCurrentUser] = useState("Robert");

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 600, margin: "0 auto" }}>
      <h1>Sophia Web UI</h1>
      <div style={{ marginBottom: 16 }}>
        <label htmlFor="user-select">Uživatel: </label>
        <select
          id="user-select"
          value={currentUser}
          onChange={(e) => setCurrentUser(e.target.value)}
          style={{ padding: "4px 8px" }}
        >
          <option value="Robert">Robert</option>
          <option value="Radek">Radek</option>
        </select>
      </div>
      <div style={{ border: "1px solid #ccc", borderRadius: 4, padding: 16, minHeight: 120 }}>
        <TaskRunner user={currentUser} />
      </div>
    </div>
  );
}

export default App;

import React, { useState, useEffect } from "react";
import { API_BASE_URL } from "./config";

const ApiStatusBadge = () => {
  const [apiStatus, setApiStatus] = useState("checking"); // "checking" | "online" | "offline"

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`, {
          signal: AbortSignal.timeout(4000),
        });
        setApiStatus(res.ok ? "online" : "offline");
      } catch {
        setApiStatus("offline");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const color =
    apiStatus === "online" ? "#4ade80"
    : apiStatus === "offline" ? "#f87171"
    : "#fbbf24";

  const label =
    apiStatus === "online" ? "API Online"
    : apiStatus === "offline" ? "API Offline"
    : "Checking...";

  return (
    <div
      title={`API ${apiStatus}`}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontSize: 12,
        color,
      }}
    >
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          backgroundColor: color,
          display: "inline-block",
          boxShadow: `0 0 6px ${color}`,
        }}
      />
      {label}
    </div>
  );
};

export default ApiStatusBadge;

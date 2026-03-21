import React, { useState } from "react";
import { API_BASE_URL } from "./config";

const WebUrlInput = ({ onProcessed }) => {
  const [webUrl, setWebUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleProcessClick = async () => {
    if (!webUrl.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/web-url`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: webUrl.trim() }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      // Assuming the API returns JSON
      const data = await response.json();

      // You can handle the response data here if needed

      onProcessed(); // notify parent that processing is done
    } catch (err) {
      setError(err.message || "Failed to process URL");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Enter web URL"
        value={webUrl}
        onChange={(e) => setWebUrl(e.target.value)}
        style={{
          padding: "10px",
          borderRadius: "4px",
          border: "1px solid #cbd5e1",
          marginBottom: "10px",
          width: "94%",
        }}
        disabled={loading}
      />
      <button
        onClick={handleProcessClick}
        style={{
          padding: "10px",
          backgroundColor: "#2563eb",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: loading ? "not-allowed" : "pointer",
          width: "100%",
          opacity: loading ? 0.6 : 1,
        }}
        disabled={loading}
      >
        {loading ? "Processing..." : "Process Web Page"}
      </button>
      {error && (
        <p style={{ color: "red", marginTop: "8px", fontSize: "0.9rem" }}>
          {error}
        </p>
      )}
    </div>
  );
};

export default WebUrlInput;

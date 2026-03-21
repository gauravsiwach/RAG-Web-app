import React from "react";

const UseExistingToggle = ({ checked, mode, onChange }) => {
  return (
    <>
      <label
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          cursor: "pointer",
          padding: "10px 12px",
          backgroundColor: checked ? "#0f4c8a" : "#334155",
          borderRadius: "8px",
          border: checked ? "1px solid #3b82f6" : "1px solid #475569",
          fontSize: "14px",
          userSelect: "none",
        }}
      >
        <input
          type="checkbox"
          checked={checked}
          onChange={onChange}
          style={{ cursor: "pointer", width: 16, height: 16 }}
        />
        💾 Use existing indexed file
      </label>

      {checked && (
        <div
          style={{
            color: "#94a3b8",
            fontSize: 13,
            padding: "12px",
            border: "1px dashed #475569",
            borderRadius: 8,
            lineHeight: 1.5,
          }}
        >
          Using previously indexed{" "}
          <strong style={{ color: "#cbd5e1" }}>
            {mode === "pdf" ? "PDF" : "web"}
          </strong>{" "}
          data. You can start chatting directly. Uncheck to upload a new{" "}
          {mode === "pdf" ? "file" : "URL"}.
        </div>
      )}
    </>
  );
};

export default UseExistingToggle;

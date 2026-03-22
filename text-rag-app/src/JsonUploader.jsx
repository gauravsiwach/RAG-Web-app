import React, { useState, useRef } from "react";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { API_BASE_URL } from "./config";

const JsonUploader = ({ onFileProcessed }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const fileInputRef = useRef(null);
  const [hover, setHover] = useState(false);

  const validateFile = (f) => {
    if (!f) return false;
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (!f.name.endsWith(".json")) {
      toast.error("Please upload a valid JSON file.");
      return false;
    }
    if (f.size > maxSize) {
      toast.error("File size exceeds 50MB limit.");
      return false;
    }
    return true;
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (validateFile(selected)) {
      setFile(selected);
    } else {
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setHover(false);
    const dropped = e.dataTransfer.files[0];
    if (validateFile(dropped)) {
      setFile(dropped);
    }
  };

  const handleProcessFile = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE_URL}/upload-json`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok)
        throw new Error(`Upload failed: ${response.statusText}`);

      const result = await response.json();
      toast.success(`JSON indexed: ${result.message || file.name}`);
      setUploadedFileName(file.name);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      onFileProcessed(file);
    } catch (error) {
      toast.error(`Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <div
        style={{
          border: "2px dashed #94a3b8",
          borderRadius: "12px",
          padding: "24px",
          backgroundColor: hover ? "#fef9c3" : "#f8fafc",
          textAlign: "center",
          color: "#475569",
          cursor: "pointer",
          marginBottom: "16px",
        }}
        onClick={() => fileInputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setHover(true); }}
        onDragLeave={() => setHover(false)}
        onDrop={handleDrop}
      >
        <div style={{ fontSize: "30px", marginBottom: "10px" }}>🗂️</div>
        <div>
          <strong>Click or drag and drop a JSON file</strong>
        </div>
        <input
          type="file"
          accept=".json,application/json"
          onChange={handleFileChange}
          disabled={uploading}
          ref={fileInputRef}
          style={{ display: "none" }}
        />
        <small style={{ color: "#64748b", display: "block", marginTop: "4px" }}>
          🗂️ Per file limit: 50MB
        </small>
        {file && (
          <small style={{ display: "block", marginTop: 10, color: "#16a34a" }}>
            {file.name}
          </small>
        )}
        {uploadedFileName && !file && (
          <small style={{ display: "block", marginTop: 10, color: "#2563eb" }}>
            ✅ Last indexed: {uploadedFileName}
          </small>
        )}
      </div>

      <button
        onClick={handleProcessFile}
        disabled={!file || uploading}
        style={{
          width: "100%",
          padding: "12px",
          backgroundColor: !file || uploading ? "#94a3b8" : "#d97706",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: !file || uploading ? "not-allowed" : "pointer",
          fontWeight: "bold",
          fontSize: "14px",
        }}
      >
        {uploading ? "⏳ Processing..." : "🗂️ Process JSON"}
      </button>
      <ToastContainer position="bottom-right" autoClose={3000} />
    </>
  );
};

export default JsonUploader;

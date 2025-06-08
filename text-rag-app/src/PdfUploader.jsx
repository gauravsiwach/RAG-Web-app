import React, { useState, useRef } from "react";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const PdfUploader = ({ onFileProcessed }) => {
  const [file, setFile] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);
  const fileInputRef = useRef(null);
  const [hover, setHover] = useState(false);

  const handleFileChange = (e) => {
    const uploaded = e.target.files[0];
    const maxSize = 50 * 1024 * 1024; // 50MB

    if (uploaded) {
      if (uploaded.type !== "application/pdf") {
        toast.error("Please upload a valid PDF.");
      } else if (uploaded.size > maxSize) {
        toast.error("File size exceeds 50MB limit.");
      } else {
        setFile(uploaded);
        return;
      }
    }

    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = ""; // clear input
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setHover(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.type === "application/pdf") {
      setFile(droppedFile);
    } else {
      toast.error("Only PDF files are allowed.");
    }
  };

  const handleProcessFile = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("chunk_size", chunkSize);
      formData.append("chunk_overlap", chunkOverlap);

      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok)
        throw new Error(`Upload failed: ${response.statusText}`);

      const result = await response.json();
      toast.success(`File processed: ${result.message || file.name}`);
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
          backgroundColor: hover ? "#e0f2fe" : "#f8fafc",
          textAlign: "center",
          color: "#475569",
          cursor: "pointer",
          marginBottom: "16px",
        }}
        onClick={() => fileInputRef.current.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setHover(true);
        }}
        onDragLeave={() => setHover(false)}
        onDrop={handleDrop}
      >
        <div style={{ fontSize: "30px", marginBottom: "10px" }}>📄</div>
        <div>
          <strong>Click or drag and drop a PDF file</strong>
        </div>
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          disabled={uploading}
          ref={fileInputRef}
          style={{ display: "none" }}
        />
        <small style={{ color: "#64748b", display: "block", marginTop: "4px" }}>
          📄 Per file limit: 50MB
        </small>
        {file && (
          <small style={{ display: "block", marginTop: 10 }}>{file.name}</small>
        )}
      </div>

      <button
        onClick={handleProcessFile}
        disabled={!file || uploading}
        style={{
          width: "100%",
          padding: "10px",
          backgroundColor: !file || uploading ? "#94a3b8" : "#0ea5e9",
          color: "#fff",
          border: "none",
          borderRadius: "8px",
          cursor: !file || uploading ? "not-allowed" : "pointer",
          fontWeight: "bold",
        }}
      >
        {uploading ? "⏳ Processing..." : "🚀 Process File"}
      </button>

      {uploadedFileName && (
        <div
          style={{ marginTop: "10px", color: "#334155", fontWeight: "bold" }}
        >
          ✅ Uploaded file: {uploadedFileName}
        </div>
      )}

      <ToastContainer position="top-right" autoClose={3000} />
    </>
  );
};

export default PdfUploader;

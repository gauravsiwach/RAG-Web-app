import React, { useState } from "react";
import PdfUploader from "./PdfUploader";
import WebUrlInput from "./WebUrlInput";
import JsonUploader from "./JsonUploader";
import ApiStatusBadge from "./ApiStatusBadge";
import UseExistingToggle from "./UseExistingToggle";
import JsonResultRenderer from "./JsonResultRenderer";
import { API_BASE_URL } from "./config";

const styles = {
  container: {
    display: "flex",
    height: "100vh",
    width: "100vw",
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  },
  sidebar: {
    width: "25%",
    backgroundColor: "#1e293b",
    color: "white",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  chat: {
    width: "75%",
    backgroundColor: "#f8fafc",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
  },
  chatHeader: { fontWeight: "bold", marginBottom: "10px" },
  chatMessages: {
    flexGrow: 1,
    overflowY: "auto",
    border: "1px solid #cbd5e1",
    padding: "10px",
    backgroundColor: "white",
  },
  chatInput: { marginTop: "10px", display: "flex" },
  input: {
    flexGrow: 1,
    padding: "10px",
    border: "1px solid #cbd5e1",
    borderRadius: "4px 0 0 4px",
  },
  button: {
    padding: "10px 20px",
    border: "none",
    backgroundColor: "#2563eb",
    color: "white",
    borderRadius: "0 4px 4px 0",
    cursor: "pointer",
  },
  disabledInput: {
    flexGrow: 1,
    padding: "10px",
    border: "1px solid #cbd5e1",
    borderRadius: "4px 0 0 4px",
    backgroundColor: "#e5e7eb",
  },
  disabledButton: {
    padding: "10px 20px",
    backgroundColor: "#94a3b8",
    color: "white",
    border: "none",
    borderRadius: "0 4px 4px 0",
    cursor: "not-allowed",
  },
};

const DashboardLayout = () => {
  const [isFileProcessed, setIsFileProcessed] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [sending, setSending] = useState(false);

  const [mode, setMode] = useState("pdf");
  const [useExisting, setUseExisting] = useState(false);

  const handleUseExistingChange = (e) => {
    const checked = e.target.checked;
    setUseExisting(checked);
    if (checked) {
      setIsFileProcessed(true);
      setChatHistory([
        {
          id: Date.now(),
          sender: "bot",
          text:
            mode === "pdf"
              ? "💾 Using existing indexed PDF. Ask your question!"
              : mode === "json"
              ? "💾 Using existing indexed JSON. Ask your question!"
              : "💾 Using existing indexed web data. Ask your question!",
        },
      ]);
    } else {
      setIsFileProcessed(false);
      setChatHistory([]);
    }
  };

  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);
  const [chunkError, setChunkError] = useState("");

  const validateChunkValues = (size, overlap) => {
    if (overlap >= size) {
      setChunkError("Chunk overlap must be less than chunk size");
    } else {
      setChunkError("");
    }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;

    const userMessage = {
      id: Date.now(),
      sender: "user",
      text: chatInput.trim(),
    };
    setChatHistory((prev) => [...prev, userMessage]);
    setChatInput("");
    setSending(true);

    try {
      // Select endpoint based on mode
      const endpoint =
        mode === "pdf"
          ? `${API_BASE_URL}/pdf_chat`
          : mode === "json"
          ? `${API_BASE_URL}/json_chat`
          : `${API_BASE_URL}/web_url_chat`;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.text }),
      });

      if (!response.ok)
        throw new Error(`Chat API error: ${response.statusText}`);

      const data = await response.json();

      const botMessage = {
        id: Date.now() + 1,
        sender: "bot",
        text: data.reply || "Sorry, I didn't get that.",
      };

      setChatHistory((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 2,
        sender: "bot",
        text: `Error: ${error.message}`,
      };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !sending && isFileProcessed) {
      handleSendMessage();
    }
  };

  const handleFileProcessed = () => {
    setIsFileProcessed(true);
    setChatHistory([
      {
        id: Date.now(),
        sender: "bot",
        text: "📘 Ask a question based on the uploaded PDF.",
      },
    ]);
  };
  const handleWebProcessed = () => {
    setIsFileProcessed(true);
    setChatHistory([
      {
        id: Date.now(),
        sender: "bot",
        text: "🌐 Ask a question based on the web page.",
      },
    ]);
  };
  const handleJsonProcessed = () => {
    setIsFileProcessed(true);
    setChatHistory([
      {
        id: Date.now(),
        sender: "bot",
        text: "🗂️ JSON indexed! Ask a question based on the uploaded JSON data.",
      },
    ]);
  };

  return (
    <div style={styles.container}>
      <style>{`
          @keyframes thinkingDots {
            0% { content: "Thinking"; }
            33% { content: "Thinking."; }
            66% { content: "Thinking.."; }
            100% { content: "Thinking..."; }
          }
          .thinking::after {
            content: "Thinking";
            animation: thinkingDots 1s steps(4, end) infinite;
          }
        `}</style>

      <div style={styles.sidebar}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>Source Configuration</h2>
          <ApiStatusBadge />
        </div>

        <div style={{ marginBottom: "0px" }}>
          <label
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 6,
            }}
          >
            <span>Chunk Size: {chunkSize}</span>
            <span>Max 4000</span>
          </label>
          <input
            type="range"
            min={100}
            max={4000}
            step={100}
            value={chunkSize}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              setChunkSize(val);
              validateChunkValues(val, chunkOverlap);
            }}
            style={{ width: "100%", marginBottom: 20 }}
          />

          <label
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 6,
            }}
          >
            <span>Chunk Overlap: {chunkOverlap}</span>
            <span>Max 1000</span>
          </label>
          <input
            type="range"
            min={0}
            max={1000}
            step={50}
            value={chunkOverlap}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              setChunkOverlap(val);
              validateChunkValues(chunkSize, val);
            }}
            style={{ width: "100%", marginBottom: 20 }}
          />
          {chunkError && (
            <div
              style={{
                color: "#f87171",
                fontSize: 12,
                marginTop: -12,
                marginBottom: 12,
              }}
            >
              {chunkError}
            </div>
          )}
        </div>

        <div style={{ marginBottom: "10px" }}>
          <label style={{ display: "block", marginBottom: "8px", fontSize: 13, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Choose Source Type
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            {[
              { value: "pdf",  icon: "📄", label: "PDF File"  },
              { value: "web",  icon: "🌐", label: "Web URL"   },
              { value: "json", icon: "🗂️", label: "JSON File" },
            ].map(({ value, icon, label }) => (
              <label
                key={value}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 7,
                  cursor: "pointer",
                  padding: "8px 10px",
                  borderRadius: 8,
                  fontSize: 13,
                  fontWeight: mode === value ? 600 : 400,
                  backgroundColor: mode === value ? "#2563eb" : "#334155",
                  border: mode === value ? "1px solid #3b82f6" : "1px solid #475569",
                  color: mode === value ? "#fff" : "#cbd5e1",
                  transition: "all 0.15s",
                  userSelect: "none",
                }}
              >
                <input
                  type="radio"
                  value={value}
                  checked={mode === value}
                  onChange={(e) => {
                    setMode(e.target.value);
                    setIsFileProcessed(false);
                    setChatHistory([]);
                    setUseExisting(false);
                  }}
                  style={{ display: "none" }}
                />
                <span>{icon}</span>
                <span>{label}</span>
              </label>
            ))}
          </div>
        </div>

        <UseExistingToggle
          checked={useExisting}
          mode={mode}
          onChange={handleUseExistingChange}
        />

        {!useExisting && (
          mode === "pdf" ? (
            <PdfUploader onFileProcessed={handleFileProcessed} />
          ) : mode === "json" ? (
            <JsonUploader onFileProcessed={handleJsonProcessed} />
          ) : (
            <WebUrlInput onProcessed={handleWebProcessed} />
          )
        )}
      </div>

      <div style={styles.chat}>
        <div style={styles.chatHeader}>
          {mode === "pdf"
            ? "Ask Your PDF (RAG Chatbot)"
            : mode === "json"
            ? "Ask Your JSON (RAG Chatbot)"
            : "Ask Your Web Page (RAG Chatbot)"}
        </div>
        <div style={styles.chatMessages} id="chatMessages">
          {!isFileProcessed && chatHistory.length === 0 && (
            <div
              style={{
                textAlign: "center",
                color: "#64748b",
                marginTop: "20px",
              }}
            >
              {mode === "pdf"
                ? '📄 Please upload and process a PDF, or check "Use existing indexed file" to chat with previously indexed data.'
                : mode === "json"
                ? '🗂️ Please upload and process a JSON file, or check "Use existing indexed file" to chat with previously indexed data.'
                : '🌐 Please enter and process a Web URL, or check "Use existing indexed file" to chat with previously indexed data.'}
            </div>
          )}

          {chatHistory.map(({ id, sender, text }) => (
            <div
              key={id}
              style={{
                display: "flex",
                justifyContent: sender === "user" ? "flex-end" : "flex-start",
                margin: "5px 0",
              }}
            >
              {sender === "bot" && (
                <span style={{ marginRight: 8, flexShrink: 0 }}>🤖</span>
              )}
              <div
                style={{
                  backgroundColor: sender === "user" ? "#2563eb" : "#e2e8f0",
                  color: sender === "user" ? "white" : "black",
                  padding: "8px 12px",
                  borderRadius: "8px",
                  maxWidth: sender === "user" ? "60%" : "80%",
                }}
              >
                {sender === "bot" && mode === "json" ? (
                  <JsonResultRenderer text={text} />
                ) : (
                  <span>{text}</span>
                )}
              </div>
              {sender === "user" && (
                <span style={{ marginLeft: 8, flexShrink: 0 }}>👤</span>
              )}
            </div>
          ))}

          {sending && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-start",
                backgroundColor: "#e2e8f0",
                color: "#334155",
                padding: "8px",
                borderRadius: "8px",
                maxWidth: "60%",
                margin: "5px 0",
                fontStyle: "italic",
              }}
            >
              <span style={{ marginRight: "8px" }}>🤖</span>
              <span className="thinking"></span>
            </div>
          )}
        </div>

        <div style={styles.chatInput}>
          <input
            type="text"
            placeholder={
              isFileProcessed
                ? "Type your message..."
                : "Upload and process a PDF first"
            }
            style={isFileProcessed ? styles.input : styles.disabledInput}
            disabled={!isFileProcessed || sending}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={handleSendMessage}
            style={
              isFileProcessed && !sending
                ? styles.button
                : styles.disabledButton
            }
            disabled={!isFileProcessed || sending || !chatInput.trim()}
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardLayout;

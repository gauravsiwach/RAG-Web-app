import React, { useState } from "react";
import PdfUploader from "./PdfUploader";

const styles = {
  container: {
    display: "flex",
    height: "100vh",
    width: "100vw",
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  },
  sidebar: {
    width: "20%",
    backgroundColor: "#1e293b",
    color: "white",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  chat: {
    width: "80%",
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
const [webUrl, setWebUrl] = useState("");

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
      const response = await fetch("http://localhost:8000/chat", {
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
        <h2>PDF Splitter Configuration</h2>
        <PdfUploader onFileProcessed={handleFileProcessed} />
      </div>

      <div style={styles.chat}>
        <div style={styles.chatHeader}>Ask Your PDF (RAG Chatbot)</div>
        <div style={styles.chatMessages} id="chatMessages">
          {!isFileProcessed && chatHistory.length === 0 && (
            <div
              style={{
                textAlign: "center",
                color: "#64748b",
                marginTop: "20px",
              }}
            >
              📄 Please upload and process a PDF to start chatting.
            </div>
          )}

          {chatHistory.map(({ id, sender, text }) => (
            <p
              key={id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: sender === "user" ? "flex-end" : "flex-start",
                backgroundColor: sender === "user" ? "#2563eb" : "#e2e8f0",
                color: sender === "user" ? "white" : "black",
                padding: "8px",
                borderRadius: "8px",
                maxWidth: "60%",
                margin: "5px 0",
                alignSelf: sender === "user" ? "flex-end" : "flex-start",
              }}
            >
              <span
                style={{
                  marginRight: sender === "user" ? "0" : "8px",
                  marginLeft: sender === "user" ? "8px" : "0",
                }}
              >
                {sender === "user" ? "👤" : "🤖"}
              </span>
              <span>{text}</span>
            </p>
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

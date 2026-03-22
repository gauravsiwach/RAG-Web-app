import React, { useMemo } from "react";

/**
 * Renders a structured JSON reply from the /json_chat endpoint.
 * If the reply contains a `data` array, renders a table.
 * Otherwise renders the `summary` as plain text.
 */
const JsonResultRenderer = ({ text }) => {
  const parsed = useMemo(() => {
    try {
      const obj = JSON.parse(text);
      if (obj && typeof obj === "object") return obj;
    } catch {
      // not JSON — fall through to plain text
    }
    return null;
  }, [text]);

  // Plain text fallback (non-JSON or error messages)
  if (!parsed) {
    return <span>{text}</span>;
  }

  const { summary, data, columns } = parsed;

  return (
    <div style={{ width: "100%" }}>
      {/* Summary sentence */}
      {summary && (
        <p style={{ margin: "0 0 10px 0", fontWeight: 500 }}>{summary}</p>
      )}

      {/* Table when data array is present */}
      {data && Array.isArray(data) && data.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: 13,
              backgroundColor: "#fff",
              borderRadius: 8,
              overflow: "hidden",
              boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
            }}
          >
            <thead>
              <tr style={{ backgroundColor: "#1e293b", color: "#fff" }}>
                {(columns || Object.keys(data[0])).map((col) => (
                  <th
                    key={col}
                    style={{
                      padding: "8px 12px",
                      textAlign: "left",
                      fontWeight: 600,
                      textTransform: "capitalize",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr
                  key={i}
                  style={{
                    backgroundColor: i % 2 === 0 ? "#f8fafc" : "#fff",
                    borderBottom: "1px solid #e2e8f0",
                  }}
                >
                  {(columns || Object.keys(data[0])).map((col) => (
                    <td
                      key={col}
                      style={{ padding: "7px 12px", verticalAlign: "top" }}
                    >
                      {row[col] !== undefined && row[col] !== null
                        ? String(row[col])
                        : "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ margin: "6px 0 0", fontSize: 12, color: "#64748b" }}>
            {data.length} result{data.length !== 1 ? "s" : ""}
          </p>
        </div>
      )}

      {/* Data was expected but came back empty */}
      {data && Array.isArray(data) && data.length === 0 && (
        <p style={{ color: "#94a3b8", fontSize: 13, margin: 0 }}>
          No matching records found.
        </p>
      )}
    </div>
  );
};

export default JsonResultRenderer;

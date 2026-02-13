"use client";

import { useState, useEffect } from "react";
import { getNodeDetail, updateNuggetStatus, type NodeDetailResponse } from "@/lib/api";

interface NodeDetailDrawerProps {
  nodeId: string | null;
  onClose: () => void;
  onExploreNugget?: (nuggetTitle: string) => void;
}

const TYPE_COLORS: Record<string, string> = {
  idea: "#4f8cf7",
  story: "#f59e0b",
  framework: "#10b981",
  definition: "#8b5cf6",
  evidence: "#ef4444",
  theme: "#ec4899",
};

export function NodeDetailDrawer({ nodeId, onClose, onExploreNugget }: NodeDetailDrawerProps) {
  const [detail, setDetail] = useState<NodeDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!nodeId) {
      setDetail(null);
      return;
    }

    setIsLoading(true);
    getNodeDetail(nodeId)
      .then(setDetail)
      .catch((err) => console.error("Failed to load node detail:", err))
      .finally(() => setIsLoading(false));
  }, [nodeId]);

  if (!nodeId) return null;

  const typeColor = TYPE_COLORS[detail?.node_type || ""] || "#6b7280";

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        bottom: 0,
        width: "400px",
        background: "#fff",
        boxShadow: "-4px 0 20px rgba(0,0,0,0.1)",
        zIndex: 100,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px",
          borderBottom: "1px solid #e0e0e0",
          display: "flex",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <button
          onClick={onClose}
          style={{
            background: "transparent",
            border: "none",
            fontSize: "18px",
            cursor: "pointer",
            color: "#888",
            padding: "4px",
          }}
        >
          x
        </button>
        <span style={{ fontWeight: 600, fontSize: "15px" }}>Node Detail</span>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: "auto", padding: "16px" }}>
        {isLoading && (
          <div style={{ color: "#888", textAlign: "center", padding: "40px" }}>
            Loading...
          </div>
        )}

        {detail && (
          <>
            {/* Title and type */}
            <div style={{ marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <span
                  style={{
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: typeColor,
                    color: "#fff",
                    fontSize: "11px",
                    fontWeight: 500,
                  }}
                >
                  {detail.node_type}
                </span>
                {detail.nugget?.score !== undefined && (
                  <span style={{ fontSize: "13px", fontWeight: 600 }}>
                    Score: {detail.nugget.score}
                  </span>
                )}
              </div>
              <h3 style={{ margin: 0, fontSize: "18px" }}>{detail.title}</h3>
              <p style={{ color: "#555", fontSize: "14px", margin: "8px 0 0 0" }}>
                {detail.summary}
              </p>
            </div>

            {/* Dimension Scores */}
            {detail.nugget?.dimension_scores && (
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ fontSize: "13px", color: "#888", marginBottom: "8px" }}>
                  Dimension Scores
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                  {Object.entries(detail.nugget.dimension_scores).map(([key, value]) => (
                    <div key={key} style={{ fontSize: "12px" }}>
                      <span style={{ color: "#888" }}>
                        {key.replace("_", " ")}:
                      </span>{" "}
                      <strong>{value}</strong>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Gap Checklist */}
            {detail.nugget?.missing_fields && detail.nugget.missing_fields.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ fontSize: "13px", color: "#888", marginBottom: "8px" }}>
                  Gaps to Fill
                </h4>
                {detail.nugget.missing_fields.map((field) => (
                  <div
                    key={field}
                    style={{
                      fontSize: "13px",
                      padding: "6px 10px",
                      background: "#fff8e1",
                      borderRadius: "4px",
                      marginBottom: "4px",
                      border: "1px solid #ffe082",
                    }}
                  >
                    Needs: {field}
                  </div>
                ))}
              </div>
            )}

            {/* Deep-dive Questions */}
            {detail.nugget?.next_questions && detail.nugget.next_questions.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ fontSize: "13px", color: "#888", marginBottom: "8px" }}>
                  Deep-dive Questions
                </h4>
                {detail.nugget.next_questions.map((q, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: "13px",
                      padding: "8px 10px",
                      background: "#e8f4fd",
                      borderRadius: "4px",
                      marginBottom: "4px",
                      color: "#0070f3",
                    }}
                  >
                    {q}
                  </div>
                ))}
              </div>
            )}

            {/* Provenance */}
            {detail.provenance.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ fontSize: "13px", color: "#888", marginBottom: "8px" }}>
                  Provenance
                </h4>
                {detail.provenance.map((p, i) => (
                  <div key={i} style={{ fontSize: "12px", color: "#666", marginBottom: "4px" }}>
                    Source: {p.source_type} | Confidence: {p.confidence} |{" "}
                    {new Date(p.timestamp).toLocaleDateString()}
                  </div>
                ))}
              </div>
            )}

            {/* Actions */}
            <div
              style={{
                display: "flex",
                gap: "8px",
                paddingTop: "16px",
                borderTop: "1px solid #e0e0e0",
              }}
            >
              <button
                onClick={() => onExploreNugget?.(detail.title)}
                style={{
                  flex: 1,
                  padding: "8px 12px",
                  background: "#0070f3",
                  color: "#fff",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Explore now
              </button>
              <button
                onClick={() => {
                  if (detail.nugget) {
                    updateNuggetStatus(detail.nugget.nugget_id, "parked");
                    onClose();
                  }
                }}
                style={{
                  padding: "8px 12px",
                  background: "transparent",
                  color: "#888",
                  border: "1px solid #ccc",
                  borderRadius: "6px",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Park
              </button>
              <button
                disabled
                title="Merge is coming in a future release"
                style={{
                  padding: "8px 12px",
                  background: "#f5f5f5",
                  color: "#ccc",
                  border: "1px solid #e0e0e0",
                  borderRadius: "6px",
                  fontSize: "13px",
                  cursor: "not-allowed",
                }}
              >
                Merge
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

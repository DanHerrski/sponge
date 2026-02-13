"use client";

import { useState } from "react";
import { onboard } from "@/lib/api";

interface OnboardingModalProps {
  onComplete: (sessionId: string) => void;
}

export function OnboardingModal({ onComplete }: OnboardingModalProps) {
  const [projectName, setProjectName] = useState("");
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim() || isLoading) return;

    setIsLoading(true);
    try {
      const response = await onboard(
        projectName.trim(),
        topic.trim() || undefined,
        audience.trim() || undefined
      );
      onComplete(response.session_id);
    } catch (error) {
      console.error("Onboarding error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const inputStyle = {
    width: "100%",
    padding: "10px 12px",
    border: "1px solid #d0d0d0",
    borderRadius: "6px",
    fontSize: "14px",
    boxSizing: "border-box" as const,
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: "12px",
          padding: "32px",
          maxWidth: "440px",
          width: "90%",
          boxShadow: "0 8px 30px rgba(0,0,0,0.15)",
        }}
      >
        <h2 style={{ margin: "0 0 4px 0", fontSize: "20px" }}>
          Start a new session
        </h2>
        <p style={{ color: "#666", fontSize: "14px", margin: "0 0 24px 0" }}>
          Give your brain dump some context so we can ask better questions.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "16px" }}>
            <label
              style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "4px" }}
            >
              Project name *
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g., Leadership book, Q3 strategy, Startup pitch"
              style={inputStyle}
              autoFocus
            />
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label
              style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "4px" }}
            >
              Topic (optional)
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., Engineering culture, Go-to-market, Product strategy"
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: "24px" }}>
            <label
              style={{ display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "4px" }}
            >
              Target audience (optional)
            </label>
            <input
              type="text"
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              placeholder="e.g., Engineering managers, Investors, First-time founders"
              style={inputStyle}
            />
          </div>

          <div style={{ display: "flex", gap: "12px" }}>
            <button
              type="submit"
              disabled={!projectName.trim() || isLoading}
              style={{
                flex: 1,
                padding: "10px",
                background: !projectName.trim() || isLoading ? "#ccc" : "#0070f3",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                fontSize: "14px",
                fontWeight: 500,
                cursor: !projectName.trim() || isLoading ? "not-allowed" : "pointer",
              }}
            >
              {isLoading ? "Creating..." : "Start session"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

"use client";

import type { NextQuestion, AlternatePath } from "@/lib/api";

interface NextQuestionCardProps {
  nextQuestion: NextQuestion | null;
  alternatePaths: AlternatePath[];
}

export function NextQuestionCard({
  nextQuestion,
  alternatePaths,
}: NextQuestionCardProps) {
  if (!nextQuestion) {
    return (
      <div style={{ padding: "16px" }}>
        <p style={{ fontWeight: 600, marginBottom: "4px" }}>Next Best Question</p>
        <p style={{ color: "#555", fontSize: "14px", margin: "0 0 8px 0" }}>
          Waiting for your first brain dump to generate questions...
        </p>
        <p style={{ color: "#888", fontSize: "12px", margin: 0 }}>
          Alternative paths will appear here.
        </p>
      </div>
    );
  }

  return (
    <div style={{ padding: "16px" }}>
      <p style={{ fontWeight: 600, marginBottom: "8px" }}>Next Best Question</p>
      <div
        style={{
          background: "#e8f4fd",
          padding: "12px",
          borderRadius: "8px",
          marginBottom: "12px",
        }}
      >
        <p
          style={{
            color: "#0070f3",
            fontSize: "15px",
            fontWeight: 500,
            margin: 0,
          }}
        >
          {nextQuestion.question}
        </p>
        <p
          style={{
            color: "#666",
            fontSize: "12px",
            margin: "8px 0 0 0",
          }}
        >
          {nextQuestion.why_this_next}
        </p>
        <p
          style={{
            color: "#888",
            fontSize: "11px",
            margin: "4px 0 0 0",
          }}
        >
          Gap: {nextQuestion.gap_type}
        </p>
      </div>

      {alternatePaths.length > 0 && (
        <div>
          <p
            style={{
              fontSize: "12px",
              color: "#888",
              marginBottom: "6px",
            }}
          >
            Alternative paths:
          </p>
          {alternatePaths.map((path, i) => (
            <div
              key={i}
              style={{
                fontSize: "13px",
                color: "#555",
                padding: "8px",
                background: "#f5f5f5",
                borderRadius: "4px",
                marginBottom: "4px",
              }}
            >
              {path.question}
              <span
                style={{
                  color: "#999",
                  fontSize: "11px",
                  marginLeft: "8px",
                }}
              >
                ({path.gap_type})
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

export function NextQuestionCard() {
  // TODO: Populate from POST /chat_turn response
  return (
    <div style={{ padding: "16px" }}>
      <p style={{ fontWeight: 600, marginBottom: "4px" }}>Next Best Question</p>
      <p style={{ color: "#555", fontSize: "14px", margin: "0 0 8px 0" }}>
        [stub] Waiting for your first brain dump to generate questions...
      </p>
      <p style={{ color: "#888", fontSize: "12px", margin: 0 }}>
        Alternative paths will appear here.
      </p>
    </div>
  );
}

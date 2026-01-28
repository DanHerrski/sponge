"use client";

export function MindMap() {
  // TODO: Integrate React Flow and fetch from GET /graph_view
  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#888",
        background: "#fafafa",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <p style={{ fontSize: "18px", marginBottom: "8px" }}>Mind Map</p>
        <p style={{ fontSize: "13px" }}>
          Knowledge graph will render here after chat turns are processed.
        </p>
      </div>
    </div>
  );
}

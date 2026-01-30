"use client";

import type { GraphNode, GraphEdge } from "@/lib/api";

interface MindMapProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function MindMap({ nodes, edges }: MindMapProps) {
  if (nodes.length === 0) {
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

  return (
    <div
      style={{
        height: "100%",
        overflow: "auto",
        padding: "16px",
        background: "#fafafa",
      }}
    >
      <div style={{ marginBottom: "16px" }}>
        <strong>Knowledge Graph</strong>
        <span style={{ color: "#888", marginLeft: "8px", fontSize: "13px" }}>
          {nodes.length} nodes, {edges.length} edges
        </span>
      </div>

      {/* Node list - placeholder until React Flow integration */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
        {nodes.map((node) => (
          <div
            key={node.node_id}
            style={{
              padding: "12px",
              background: "#fff",
              border: "1px solid #e0e0e0",
              borderRadius: "8px",
              minWidth: "200px",
              maxWidth: "280px",
            }}
          >
            <div style={{ fontWeight: 500, marginBottom: "4px" }}>
              {node.title}
            </div>
            <div
              style={{
                fontSize: "12px",
                color: "#666",
                marginBottom: "8px",
              }}
            >
              {node.node_type}
              {node.score !== null && ` • Score: ${node.score}`}
            </div>
            <div style={{ fontSize: "13px", color: "#444" }}>
              {node.summary}
            </div>
          </div>
        ))}
      </div>

      {/* Edge list */}
      {edges.length > 0 && (
        <div style={{ marginTop: "16px", fontSize: "12px", color: "#888" }}>
          <strong>Connections:</strong>
          <ul style={{ margin: "8px 0", paddingLeft: "20px" }}>
            {edges.map((edge) => {
              const sourceNode = nodes.find((n) => n.node_id === edge.source_id);
              const targetNode = nodes.find((n) => n.node_id === edge.target_id);
              return (
                <li key={edge.edge_id}>
                  {sourceNode?.title || edge.source_id} →{" "}
                  {targetNode?.title || edge.target_id} ({edge.edge_type})
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

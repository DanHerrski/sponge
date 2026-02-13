"use client";

import { useMemo, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node as RFNode,
  type Edge as RFEdge,
  type NodeMouseHandler,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { GraphNode, GraphEdge } from "@/lib/api";

interface MindMapProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string) => void;
}

const NODE_TYPE_COLORS: Record<string, string> = {
  idea: "#4f8cf7",
  story: "#f59e0b",
  framework: "#10b981",
  definition: "#8b5cf6",
  evidence: "#ef4444",
  theme: "#ec4899",
};

function buildLayout(nodes: GraphNode[]): RFNode[] {
  // Simple radial layout: place nodes in a circle
  const cx = 400;
  const cy = 300;
  const radius = Math.max(150, nodes.length * 40);

  return nodes.map((node, i) => {
    const angle = (2 * Math.PI * i) / Math.max(nodes.length, 1);
    const color = NODE_TYPE_COLORS[node.node_type] || "#6b7280";
    return {
      id: node.node_id,
      position: {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      },
      data: {
        label: node.title,
        nodeType: node.node_type,
        score: node.score,
        summary: node.summary,
      },
      style: {
        background: color,
        color: "#fff",
        border: `2px solid ${color}`,
        borderRadius: "8px",
        padding: "10px 14px",
        fontSize: "13px",
        fontWeight: 500,
        maxWidth: "200px",
        textAlign: "center" as const,
      },
    };
  });
}

const EDGE_TYPE_STYLES: Record<string, { stroke: string; strokeDasharray?: string }> = {
  supports: { stroke: "#10b981" },
  example_of: { stroke: "#f59e0b" },
  expands_on: { stroke: "#4f8cf7" },
  related_to: { stroke: "#9ca3af", strokeDasharray: "5,5" },
  contradicts: { stroke: "#ef4444", strokeDasharray: "3,3" },
};

function buildEdges(edges: GraphEdge[]): RFEdge[] {
  return edges.map((edge) => {
    const style = EDGE_TYPE_STYLES[edge.edge_type] || { stroke: "#9ca3af" };
    return {
      id: edge.edge_id,
      source: edge.source_id,
      target: edge.target_id,
      label: edge.edge_type.replace("_", " "),
      style: { stroke: style.stroke, strokeDasharray: style.strokeDasharray },
      markerEnd: { type: MarkerType.ArrowClosed, color: style.stroke },
      labelStyle: { fontSize: "10px", fill: "#888" },
    };
  });
}

export function MindMap({ nodes, edges, onNodeClick }: MindMapProps) {
  const rfNodes = useMemo(() => buildLayout(nodes), [nodes]);
  const rfEdges = useMemo(() => buildEdges(edges), [edges]);

  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState(rfNodes);
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState(rfEdges);

  // Sync when props change
  useMemo(() => {
    setFlowNodes(rfNodes);
    setFlowEdges(rfEdges);
  }, [rfNodes, rfEdges, setFlowNodes, setFlowEdges]);

  const handleNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

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
            Knowledge graph will appear here after your first brain dump.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: "100%", background: "#fafafa" }}>
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.3}
        maxZoom={2}
      >
        <Background color="#e0e0e0" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const nt = node.data?.nodeType as string;
            return NODE_TYPE_COLORS[nt] || "#6b7280";
          }}
          style={{ background: "#f5f5f5" }}
        />
      </ReactFlow>
    </div>
  );
}

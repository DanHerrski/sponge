"use client";

import { useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { MindMap } from "@/components/MindMap";
import { NextQuestionCard } from "@/components/NextQuestionCard";
import type {
  ChatTurnResponse,
  GraphNode,
  GraphEdge,
  NextQuestion,
  AlternatePath,
} from "@/lib/api";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [nextQuestion, setNextQuestion] = useState<NextQuestion | null>(null);
  const [alternatePaths, setAlternatePaths] = useState<AlternatePath[]>([]);

  const handleSessionCreated = (newSessionId: string) => {
    setSessionId(newSessionId);
  };

  const handleGraphUpdate = (response: ChatTurnResponse) => {
    setNodes(response.graph_nodes);
    setEdges(response.graph_edges);
    setNextQuestion(response.next_question);
    setAlternatePaths(response.alternate_paths);
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Left: Chat panel */}
      <div style={{ flex: 1, borderRight: "1px solid #e0e0e0", display: "flex", flexDirection: "column" }}>
        <ChatPanel
          sessionId={sessionId}
          onSessionCreated={handleSessionCreated}
          onGraphUpdate={handleGraphUpdate}
        />
      </div>

      {/* Right: Mind map + Next question */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1 }}>
          <MindMap nodes={nodes} edges={edges} />
        </div>
        <div style={{ borderTop: "1px solid #e0e0e0" }}>
          <NextQuestionCard
            nextQuestion={nextQuestion}
            alternatePaths={alternatePaths}
          />
        </div>
      </div>
    </div>
  );
}

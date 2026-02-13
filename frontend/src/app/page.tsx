"use client";

import { useState, useCallback } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { MindMap } from "@/components/MindMap";
import { NextQuestionCard } from "@/components/NextQuestionCard";
import { NuggetInbox } from "@/components/NuggetInbox";
import { NodeDetailDrawer } from "@/components/NodeDetailDrawer";
import { OnboardingModal } from "@/components/OnboardingModal";
import { UploadButton } from "@/components/UploadButton";
import type {
  ChatTurnResponse,
  GraphNode,
  GraphEdge,
  NextQuestion,
  AlternatePath,
  UploadResponse,
} from "@/lib/api";

type RightTab = "map" | "inbox";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(true);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [nextQuestion, setNextQuestion] = useState<NextQuestion | null>(null);
  const [alternatePaths, setAlternatePaths] = useState<AlternatePath[]>([]);
  const [rightTab, setRightTab] = useState<RightTab>("map");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [inboxRefreshTrigger, setInboxRefreshTrigger] = useState(0);

  const handleOnboardingComplete = (newSessionId: string) => {
    setSessionId(newSessionId);
    setShowOnboarding(false);
  };

  const handleSkipOnboarding = () => {
    setShowOnboarding(false);
  };

  const handleSessionCreated = (newSessionId: string) => {
    setSessionId(newSessionId);
  };

  const handleGraphUpdate = useCallback((response: ChatTurnResponse) => {
    setNodes(response.graph_nodes);
    setEdges(response.graph_edges);
    setNextQuestion(response.next_question);
    setAlternatePaths(response.alternate_paths);
    setInboxRefreshTrigger((prev) => prev + 1);
  }, []);

  const handleUploadComplete = useCallback((_response: UploadResponse) => {
    setInboxRefreshTrigger((prev) => prev + 1);
  }, []);

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
  }, []);

  const handleExploreNugget = useCallback((_title: string) => {
    setSelectedNodeId(null);
  }, []);

  const tabStyle = (active: boolean) => ({
    padding: "8px 16px",
    background: active ? "#0070f3" : "transparent",
    color: active ? "#fff" : "#555",
    border: "none",
    borderRadius: "6px 6px 0 0",
    fontSize: "13px",
    fontWeight: active ? 600 : 400,
    cursor: "pointer" as const,
  });

  return (
    <>
      {showOnboarding && (
        <div>
          <OnboardingModal onComplete={handleOnboardingComplete} />
          <button
            onClick={handleSkipOnboarding}
            style={{
              position: "fixed",
              bottom: "20px",
              left: "50%",
              transform: "translateX(-50%)",
              background: "transparent",
              border: "none",
              color: "#888",
              fontSize: "13px",
              cursor: "pointer",
              zIndex: 1001,
              textDecoration: "underline",
            }}
          >
            Skip for now
          </button>
        </div>
      )}

      <div style={{ display: "flex", height: "100vh" }}>
        {/* Left: Chat panel + upload */}
        <div
          style={{
            flex: 1,
            borderRight: "1px solid #e0e0e0",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <ChatPanel
            sessionId={sessionId}
            onSessionCreated={handleSessionCreated}
            onGraphUpdate={handleGraphUpdate}
          />
          <div
            style={{
              padding: "8px 12px",
              borderTop: "1px solid #f0f0f0",
              display: "flex",
              gap: "8px",
              alignItems: "center",
            }}
          >
            <UploadButton
              sessionId={sessionId}
              onUploadComplete={handleUploadComplete}
            />
          </div>
        </div>

        {/* Right: Tabs (Map / Inbox) + Next question */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          {/* Tab bar */}
          <div
            style={{
              display: "flex",
              gap: "4px",
              padding: "8px 12px 0 12px",
              borderBottom: "1px solid #e0e0e0",
              background: "#fafafa",
            }}
          >
            <button
              style={tabStyle(rightTab === "map")}
              onClick={() => setRightTab("map")}
            >
              Mind Map
            </button>
            <button
              style={tabStyle(rightTab === "inbox")}
              onClick={() => setRightTab("inbox")}
            >
              Nugget Inbox
            </button>
          </div>

          {/* Tab content */}
          <div style={{ flex: 1, overflow: "hidden" }}>
            {rightTab === "map" ? (
              <MindMap
                nodes={nodes}
                edges={edges}
                onNodeClick={handleNodeClick}
              />
            ) : (
              <NuggetInbox
                sessionId={sessionId}
                refreshTrigger={inboxRefreshTrigger}
                onExploreNugget={handleExploreNugget}
                onSelectNugget={handleNodeClick}
              />
            )}
          </div>

          {/* Next question card */}
          <div style={{ borderTop: "1px solid #e0e0e0" }}>
            <NextQuestionCard
              nextQuestion={nextQuestion}
              alternatePaths={alternatePaths}
            />
          </div>
        </div>
      </div>

      {/* Node Detail Drawer (slide-out) */}
      <NodeDetailDrawer
        nodeId={selectedNodeId}
        onClose={() => setSelectedNodeId(null)}
        onExploreNugget={handleExploreNugget}
      />
    </>
  );
}

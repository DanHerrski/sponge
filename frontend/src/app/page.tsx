"use client";

import { ChatPanel } from "@/components/ChatPanel";
import { MindMap } from "@/components/MindMap";
import { NextQuestionCard } from "@/components/NextQuestionCard";

export default function Home() {
  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Left: Chat panel */}
      <div style={{ flex: 1, borderRight: "1px solid #e0e0e0", display: "flex", flexDirection: "column" }}>
        <ChatPanel />
      </div>

      {/* Right: Mind map + Next question */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1 }}>
          <MindMap />
        </div>
        <div style={{ borderTop: "1px solid #e0e0e0" }}>
          <NextQuestionCard />
        </div>
      </div>
    </div>
  );
}

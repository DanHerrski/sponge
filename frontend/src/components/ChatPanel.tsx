"use client";

import { useState } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // TODO: Call POST /chat_turn and parse structured response
    const stubResponse: Message = {
      role: "assistant",
      content: "[stub] Nuggets extracted. Next question will appear below.",
    };
    setMessages((prev) => [...prev, stubResponse]);
  };

  return (
    <>
      <div style={{ padding: "16px", borderBottom: "1px solid #e0e0e0" }}>
        <strong>Sponge</strong> — Brain Dump Chat
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: "16px" }}>
        {messages.length === 0 && (
          <p style={{ color: "#888" }}>
            Start typing to brain-dump your ideas. The system will extract
            nuggets, build your knowledge graph, and suggest what to explore
            next.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: "12px",
              textAlign: msg.role === "user" ? "right" : "left",
            }}
          >
            <span
              style={{
                display: "inline-block",
                padding: "8px 12px",
                borderRadius: "8px",
                background: msg.role === "user" ? "#0070f3" : "#f0f0f0",
                color: msg.role === "user" ? "#fff" : "#000",
                maxWidth: "80%",
              }}
            >
              {msg.content}
            </span>
          </div>
        ))}
      </div>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", padding: "12px", borderTop: "1px solid #e0e0e0" }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your brain dump here..."
          style={{
            flex: 1,
            padding: "10px",
            border: "1px solid #ccc",
            borderRadius: "6px",
            fontSize: "14px",
          }}
        />
        <button
          type="submit"
          style={{
            marginLeft: "8px",
            padding: "10px 20px",
            background: "#0070f3",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          Send
        </button>
      </form>
    </>
  );
}

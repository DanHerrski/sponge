"use client";

import { useState } from "react";
import {
  sendChatTurn,
  isExtractionFailure,
  type ChatTurnResponse,
  type ExtractionFailureResponse,
  type CapturedNugget,
} from "../lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  nuggets?: CapturedNugget[];
  nextQuestion?: string;
  isFailure?: boolean;
}

interface ChatPanelProps {
  sessionId: string | null;
  onSessionCreated: (sessionId: string) => void;
  onGraphUpdate: (response: ChatTurnResponse) => void;
}

export function ChatPanel({
  sessionId,
  onSessionCreated,
  onGraphUpdate,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendChatTurn(input, sessionId || undefined);

      // Update session ID if this was the first message
      if (!sessionId && response.session_id) {
        onSessionCreated(response.session_id);
      }

      if (isExtractionFailure(response)) {
        // Handle extraction failure
        const failureResponse = response as ExtractionFailureResponse;
        const assistantMessage: Message = {
          role: "assistant",
          content: `${failureResponse.failure_reason} ${failureResponse.recovery_question}`,
          isFailure: true,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        // Handle successful extraction
        const successResponse = response as ChatTurnResponse;

        // Build assistant message content
        let content = successResponse.graph_update_summary;
        if (successResponse.next_question) {
          content += ` ${successResponse.next_question.question}`;
        }

        const assistantMessage: Message = {
          role: "assistant",
          content,
          nuggets: successResponse.captured_nuggets,
          nextQuestion: successResponse.next_question?.question,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // Notify parent of graph update
        onGraphUpdate(successResponse);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: Message = {
        role: "assistant",
        content:
          "Sorry, there was an error processing your message. Please try again.",
        isFailure: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div style={{ padding: "16px", borderBottom: "1px solid #e0e0e0" }}>
        <strong>Sponge</strong> — Brain Dump Chat
        {sessionId && (
          <span style={{ fontSize: "12px", color: "#888", marginLeft: "8px" }}>
            Session: {sessionId.slice(0, 8)}...
          </span>
        )}
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
              marginBottom: "16px",
              textAlign: msg.role === "user" ? "right" : "left",
            }}
          >
            <span
              style={{
                display: "inline-block",
                padding: "10px 14px",
                borderRadius: "8px",
                background: msg.role === "user"
                  ? "#0070f3"
                  : msg.isFailure
                  ? "#fff3cd"
                  : "#f0f0f0",
                color: msg.role === "user" ? "#fff" : "#000",
                maxWidth: "85%",
                textAlign: "left",
              }}
            >
              {msg.content}

              {/* Show captured nuggets */}
              {msg.nuggets && msg.nuggets.length > 0 && (
                <div
                  style={{
                    marginTop: "12px",
                    paddingTop: "12px",
                    borderTop: "1px solid #ddd",
                  }}
                >
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#666",
                      marginBottom: "8px",
                    }}
                  >
                    Captured nuggets:
                  </div>
                  {msg.nuggets.map((nugget) => (
                    <div
                      key={nugget.nugget_id}
                      style={{
                        background: "#fff",
                        padding: "8px",
                        borderRadius: "4px",
                        marginBottom: "6px",
                        border: "1px solid #e0e0e0",
                      }}
                    >
                      <div style={{ fontWeight: 500, fontSize: "14px" }}>
                        {nugget.title}
                      </div>
                      <div
                        style={{
                          fontSize: "12px",
                          color: "#666",
                          marginTop: "4px",
                        }}
                      >
                        {nugget.nugget_type} • Score: {nugget.score}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </span>
          </div>
        ))}
        {isLoading && (
          <div style={{ textAlign: "left", marginBottom: "16px" }}>
            <span
              style={{
                display: "inline-block",
                padding: "10px 14px",
                borderRadius: "8px",
                background: "#f0f0f0",
                color: "#888",
              }}
            >
              Extracting nuggets...
            </span>
          </div>
        )}
      </div>
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          padding: "12px",
          borderTop: "1px solid #e0e0e0",
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your brain dump here..."
          disabled={isLoading}
          style={{
            flex: 1,
            padding: "10px",
            border: "1px solid #ccc",
            borderRadius: "6px",
            fontSize: "14px",
            opacity: isLoading ? 0.7 : 1,
          }}
        />
        <button
          type="submit"
          disabled={isLoading}
          style={{
            marginLeft: "8px",
            padding: "10px 20px",
            background: isLoading ? "#ccc" : "#0070f3",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: isLoading ? "not-allowed" : "pointer",
            fontSize: "14px",
          }}
        >
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </>
  );
}

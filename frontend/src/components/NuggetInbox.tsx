"use client";

import { useState, useEffect, useCallback } from "react";
import {
  listNuggets,
  updateNuggetStatus,
  type NuggetListItem,
} from "@/lib/api";

interface NuggetInboxProps {
  sessionId: string | null;
  refreshTrigger: number;
  onExploreNugget?: (nuggetTitle: string) => void;
  onSelectNugget?: (nodeId: string) => void;
}

const TYPE_COLORS: Record<string, string> = {
  idea: "#4f8cf7",
  story: "#f59e0b",
  framework: "#10b981",
};

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  new: { bg: "#e8f4fd", text: "#0070f3" },
  explored: { bg: "#d4edda", text: "#155724" },
  parked: { bg: "#f0f0f0", text: "#888" },
};

export function NuggetInbox({
  sessionId,
  refreshTrigger,
  onExploreNugget,
  onSelectNugget,
}: NuggetInboxProps) {
  const [nuggets, setNuggets] = useState<NuggetListItem[]>([]);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"score" | "created_at">("score");

  const fetchNuggets = useCallback(async () => {
    if (!sessionId) return;
    try {
      const response = await listNuggets(sessionId, {
        nuggetType: typeFilter || undefined,
        status: statusFilter || undefined,
        sortBy,
      });
      setNuggets(response.nuggets);
    } catch (error) {
      console.error("Failed to fetch nuggets:", error);
    }
  }, [sessionId, typeFilter, statusFilter, sortBy]);

  useEffect(() => {
    fetchNuggets();
  }, [fetchNuggets, refreshTrigger]);

  const handleStatusChange = async (nuggetId: string, newStatus: "new" | "explored" | "parked") => {
    try {
      await updateNuggetStatus(nuggetId, newStatus);
      fetchNuggets();
    } catch (error) {
      console.error("Failed to update status:", error);
    }
  };

  // Client-side keyword search
  const filtered = nuggets.filter((n) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return n.title.toLowerCase().includes(q) || n.short_summary.toLowerCase().includes(q);
  });

  if (!sessionId) {
    return (
      <div style={{ padding: "16px", color: "#888", fontSize: "14px" }}>
        Start a session to see your nugget inbox.
      </div>
    );
  }

  return (
    <div style={{ padding: "12px", height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ marginBottom: "12px" }}>
        <strong style={{ fontSize: "15px" }}>Nugget Inbox</strong>
        <span style={{ color: "#888", fontSize: "12px", marginLeft: "8px" }}>
          {filtered.length} nugget{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search..."
          style={{
            flex: 1,
            minWidth: "120px",
            padding: "6px 10px",
            border: "1px solid #d0d0d0",
            borderRadius: "4px",
            fontSize: "12px",
          }}
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          style={{ padding: "6px", border: "1px solid #d0d0d0", borderRadius: "4px", fontSize: "12px" }}
        >
          <option value="">All types</option>
          <option value="idea">Idea</option>
          <option value="story">Story</option>
          <option value="framework">Framework</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ padding: "6px", border: "1px solid #d0d0d0", borderRadius: "4px", fontSize: "12px" }}
        >
          <option value="">All status</option>
          <option value="new">New</option>
          <option value="explored">Explored</option>
          <option value="parked">Parked</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "score" | "created_at")}
          style={{ padding: "6px", border: "1px solid #d0d0d0", borderRadius: "4px", fontSize: "12px" }}
        >
          <option value="score">Sort: Score</option>
          <option value="created_at">Sort: Recent</option>
        </select>
      </div>

      {/* Nugget list */}
      <div style={{ flex: 1, overflow: "auto" }}>
        {filtered.length === 0 && (
          <div style={{ color: "#888", fontSize: "13px", textAlign: "center", padding: "20px" }}>
            {nuggets.length === 0 ? "No nuggets yet." : "No nuggets match your filters."}
          </div>
        )}
        {filtered.map((nugget) => {
          const typeColor = TYPE_COLORS[nugget.nugget_type] || "#6b7280";
          const statusStyle = STATUS_COLORS[nugget.status] || STATUS_COLORS.new;

          return (
            <div
              key={nugget.nugget_id}
              style={{
                padding: "10px 12px",
                borderBottom: "1px solid #f0f0f0",
                cursor: "pointer",
              }}
              onClick={() => onSelectNugget?.(nugget.node_id)}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                <span
                  style={{
                    display: "inline-block",
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: typeColor,
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontWeight: 500, fontSize: "13px", flex: 1 }}>
                  {nugget.title}
                </span>
                <span style={{ fontSize: "12px", fontWeight: 600, color: "#444" }}>
                  {nugget.score}
                </span>
              </div>

              <div style={{ fontSize: "12px", color: "#666", marginBottom: "6px", marginLeft: "16px" }}>
                {nugget.short_summary.slice(0, 100)}
                {nugget.short_summary.length > 100 ? "..." : ""}
              </div>

              <div style={{ display: "flex", gap: "6px", marginLeft: "16px", alignItems: "center" }}>
                <span
                  style={{
                    fontSize: "10px",
                    padding: "2px 6px",
                    borderRadius: "3px",
                    background: statusStyle.bg,
                    color: statusStyle.text,
                    fontWeight: 500,
                  }}
                >
                  {nugget.status}
                </span>
                <span style={{ fontSize: "10px", color: "#999" }}>
                  {nugget.nugget_type}
                </span>
                {nugget.missing_fields.length > 0 && (
                  <span style={{ fontSize: "10px", color: "#999" }}>
                    Gaps: {nugget.missing_fields.join(", ")}
                  </span>
                )}
                <span style={{ flex: 1 }} />
                {nugget.status !== "explored" && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStatusChange(nugget.nugget_id, "explored");
                      onExploreNugget?.(nugget.title);
                    }}
                    style={{
                      fontSize: "10px",
                      padding: "2px 8px",
                      border: "1px solid #0070f3",
                      borderRadius: "3px",
                      background: "transparent",
                      color: "#0070f3",
                      cursor: "pointer",
                    }}
                  >
                    Explore
                  </button>
                )}
                {nugget.status !== "parked" && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStatusChange(nugget.nugget_id, "parked");
                    }}
                    style={{
                      fontSize: "10px",
                      padding: "2px 8px",
                      border: "1px solid #ccc",
                      borderRadius: "3px",
                      background: "transparent",
                      color: "#888",
                      cursor: "pointer",
                    }}
                  >
                    Park
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Sponge API Edge Function
// Implements steel-thread API routes using Supabase

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0";

// --- Configuration ---

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY") || "";

// CORS configuration
const ALLOWED_ORIGINS = [
  "http://localhost:3000",
  "http://localhost:5173",
  "https://danherrski.github.io", // Update with your GitHub Pages URL
];

// Minimum score threshold for valid nuggets
const MIN_SCORE_THRESHOLD = 30;

// Recovery questions for extraction failures
const RECOVERY_QUESTIONS = [
  "Can you give me a concrete example of what you mean?",
  "What decision or mistake does this relate to?",
  "Who specifically would benefit from this idea?",
  "What's the one thing you'd want someone to remember from this?",
  "Can you tell me a short story that illustrates this?",
];

// --- Types ---

interface ChatTurnRequest {
  session_id?: string;
  message: string;
}

interface NuggetFeedbackRequest {
  feedback: "up" | "down";
}

interface NodeEditRequest {
  title?: string;
  summary?: string;
}

interface UploadRequest {
  session_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
}

interface ExtractedNugget {
  nugget_type: "idea" | "story" | "framework";
  title: string;
  summary: string;
  confidence: "high" | "medium" | "low";
  dimension_scores: {
    specificity: number;
    novelty: number;
    authority: number;
    actionability: number;
    story_energy: number;
    audience_resonance: number;
  };
  missing_fields: string[];
}

// --- Helpers ---

function corsHeaders(origin: string): HeadersInit {
  const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allowedOrigin,
    "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
  };
}

function jsonResponse(data: unknown, status = 200, origin = ""): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(origin),
    },
  });
}

function errorResponse(message: string, status = 400, origin = ""): Response {
  return jsonResponse({ error: message }, status, origin);
}

function selectRecoveryQuestion(turnNumber: number): string {
  return RECOVERY_QUESTIONS[turnNumber % RECOVERY_QUESTIONS.length];
}

function calculateTotalScore(scores: ExtractedNugget["dimension_scores"]): number {
  const weights = {
    specificity: 0.20,
    novelty: 0.15,
    authority: 0.20,
    actionability: 0.15,
    story_energy: 0.15,
    audience_resonance: 0.15,
  };
  return Math.round(
    scores.specificity * weights.specificity +
    scores.novelty * weights.novelty +
    scores.authority * weights.authority +
    scores.actionability * weights.actionability +
    scores.story_energy * weights.story_energy +
    scores.audience_resonance * weights.audience_resonance
  );
}

// --- LLM Integration (Stub Mode) ---

async function extractNuggets(message: string, _context: string): Promise<ExtractedNugget[]> {
  // In production, this would call OpenAI/Anthropic
  // For now, return stub extraction
  if (OPENAI_API_KEY && OPENAI_API_KEY !== "stub") {
    // TODO: Implement real LLM extraction
    // For now, fall through to stub
  }

  // Stub extraction - returns a single nugget based on input
  const stubScores = {
    specificity: 65,
    novelty: 55,
    authority: 60,
    actionability: 70,
    story_energy: 50,
    audience_resonance: 60,
  };

  return [{
    nugget_type: "idea",
    title: `Insight from: "${message.slice(0, 50)}${message.length > 50 ? '...' : ''}"`,
    summary: `Extracted insight from user input. ${message.slice(0, 150)}${message.length > 150 ? '...' : ''}`,
    confidence: "medium",
    dimension_scores: stubScores,
    missing_fields: ["example", "evidence"],
  }];
}

async function generateNextQuestions(
  nuggets: Array<{ title: string; nugget_id: string }>,
): Promise<{
  primary: { question: string; target_nugget_id: string; gap_type: string };
  alternates: Array<{ question: string; target_nugget_id: string; gap_type: string }>;
  why_primary: string;
}> {
  if (nuggets.length === 0) {
    return {
      primary: {
        question: "What's the most important idea you'd like to explore?",
        target_nugget_id: "",
        gap_type: "example",
      },
      alternates: [],
      why_primary: "Let's start by identifying your core insight.",
    };
  }

  const target = nuggets[0];
  return {
    primary: {
      question: `Can you give me a specific example of "${target.title}"?`,
      target_nugget_id: target.nugget_id,
      gap_type: "example",
    },
    alternates: [
      {
        question: `What outcome did you see when applying this?`,
        target_nugget_id: target.nugget_id,
        gap_type: "outcome",
      },
      {
        question: `Who would benefit most from this insight?`,
        target_nugget_id: target.nugget_id,
        gap_type: "audience",
      },
    ],
    why_primary: "A concrete example would make this insight more compelling and memorable.",
  };
}

// --- Route Handlers ---

async function handleChatTurn(
  supabase: ReturnType<typeof createClient>,
  body: ChatTurnRequest,
  origin: string,
): Promise<Response> {
  const { session_id, message } = body;

  if (!message || message.trim().length === 0) {
    return errorResponse("Message is required", 400, origin);
  }

  // Create or get session
  let sessionId = session_id;
  if (!sessionId) {
    const { data: session, error: sessionError } = await supabase
      .from("sessions")
      .insert({ project_name: "Untitled" })
      .select("id")
      .single();

    if (sessionError) {
      return errorResponse(`Failed to create session: ${sessionError.message}`, 500, origin);
    }
    sessionId = session.id;
  }

  // Get next turn number
  const { data: lastTurn } = await supabase
    .from("chat_turns")
    .select("turn_number")
    .eq("session_id", sessionId)
    .order("turn_number", { ascending: false })
    .limit(1)
    .single();

  const nextTurnNumber = (lastTurn?.turn_number || 0) + 1;

  // Store user message
  const { data: userTurn, error: turnError } = await supabase
    .from("chat_turns")
    .insert({
      session_id: sessionId,
      turn_number: nextTurnNumber,
      role: "user",
      content: message,
    })
    .select("id")
    .single();

  if (turnError) {
    return errorResponse(`Failed to store chat turn: ${turnError.message}`, 500, origin);
  }

  // Get session context (existing high-value nuggets)
  const { data: existingNuggets } = await supabase
    .from("nuggets")
    .select("title, short_summary")
    .eq("status", "new")
    .gte("score", 60)
    .order("score", { ascending: false })
    .limit(5);

  const sessionContext = existingNuggets
    ?.map((n: { title: string }) => n.title)
    .join(", ") || "";

  // Extract nuggets
  const extractedNuggets = await extractNuggets(message, sessionContext);

  // Check for extraction failure
  if (extractedNuggets.length === 0) {
    const recoveryQuestion = selectRecoveryQuestion(nextTurnNumber);
    const failureReason = "I couldn't identify any distinct ideas from what you shared.";

    // Store assistant response
    await supabase.from("chat_turns").insert({
      session_id: sessionId,
      turn_number: nextTurnNumber + 1,
      role: "assistant",
      content: `I'm not sure I fully captured that. ${failureReason} ${recoveryQuestion}`,
    });

    return jsonResponse({
      turn_id: userTurn.id,
      session_id: sessionId,
      extraction_failed: true,
      failure_reason: failureReason,
      recovery_question: recoveryQuestion,
      captured_nuggets: [],
      graph_update_summary: "",
    }, 200, origin);
  }

  // Filter and score nuggets
  const validNuggets = extractedNuggets.filter(n => {
    const score = calculateTotalScore(n.dimension_scores);
    return score >= MIN_SCORE_THRESHOLD;
  });

  if (validNuggets.length === 0) {
    const recoveryQuestion = selectRecoveryQuestion(nextTurnNumber);
    const failureReason = "The ideas I captured seem too vague or general to be useful.";

    await supabase.from("chat_turns").insert({
      session_id: sessionId,
      turn_number: nextTurnNumber + 1,
      role: "assistant",
      content: `I'm not sure I fully captured that. ${failureReason} ${recoveryQuestion}`,
    });

    return jsonResponse({
      turn_id: userTurn.id,
      session_id: sessionId,
      extraction_failed: true,
      failure_reason: failureReason,
      recovery_question: recoveryQuestion,
      captured_nuggets: [],
      graph_update_summary: "",
    }, 200, origin);
  }

  // Create nodes and nuggets
  const capturedNuggets = [];
  for (const nugget of validNuggets) {
    const totalScore = calculateTotalScore(nugget.dimension_scores);

    // Create node
    const { data: node, error: nodeError } = await supabase
      .from("nodes")
      .insert({
        session_id: sessionId,
        node_type: nugget.nugget_type,
        title: nugget.title,
        summary: nugget.summary,
      })
      .select("id")
      .single();

    if (nodeError) {
      console.error("Failed to create node:", nodeError);
      continue;
    }

    // Create nugget
    const { data: nuggetRecord, error: nuggetError } = await supabase
      .from("nuggets")
      .insert({
        node_id: node.id,
        nugget_type: nugget.nugget_type,
        title: nugget.title,
        short_summary: nugget.summary.slice(0, 200),
        score: totalScore,
        dimension_scores: nugget.dimension_scores,
        missing_fields: nugget.missing_fields,
        status: "new",
      })
      .select("id")
      .single();

    if (nuggetError) {
      console.error("Failed to create nugget:", nuggetError);
      continue;
    }

    // Create provenance
    await supabase.from("provenance").insert({
      node_id: node.id,
      source_type: "chat",
      source_id: userTurn.id,
      confidence: nugget.confidence,
    });

    capturedNuggets.push({
      nugget_id: nuggetRecord.id,
      node_id: node.id,
      title: nugget.title,
      nugget_type: nugget.nugget_type.charAt(0).toUpperCase() + nugget.nugget_type.slice(1),
      score: totalScore,
      is_new: true,
      user_feedback: null,
      dimension_scores: nugget.dimension_scores,
    });
  }

  // Generate next questions
  const questions = await generateNextQuestions(
    capturedNuggets.map(n => ({ title: n.title, nugget_id: n.nugget_id }))
  );

  // Get graph subset
  const { data: nodes } = await supabase
    .from("nodes")
    .select(`
      id,
      node_type,
      title,
      summary,
      nuggets (score)
    `)
    .eq("session_id", sessionId)
    .order("created_at", { ascending: false })
    .limit(20);

  const { data: edges } = await supabase
    .from("edges")
    .select("id, source_id, target_id, edge_type")
    .eq("session_id", sessionId);

  const graphNodes = (nodes || []).map((n: any) => ({
    node_id: n.id,
    node_type: n.node_type,
    title: n.title,
    summary: n.summary,
    score: n.nuggets?.[0]?.score || null,
  }));

  const graphEdges = (edges || []).map((e: any) => ({
    edge_id: e.id,
    source_id: e.source_id,
    target_id: e.target_id,
    edge_type: e.edge_type,
  }));

  // Build summary
  const nodeCount = capturedNuggets.length;
  const graphUpdateSummary = `Added ${nodeCount} new node${nodeCount !== 1 ? 's' : ''} to your knowledge graph.`;

  // Store assistant response
  const nuggetTitles = capturedNuggets.slice(0, 3).map(n => n.title).join(", ");
  await supabase.from("chat_turns").insert({
    session_id: sessionId,
    turn_number: nextTurnNumber + 1,
    role: "assistant",
    content: `Captured: ${nuggetTitles}. ${graphUpdateSummary} ${questions.primary.question}`,
  });

  return jsonResponse({
    turn_id: userTurn.id,
    session_id: sessionId,
    captured_nuggets: capturedNuggets,
    graph_update_summary: graphUpdateSummary,
    next_question: questions.primary.target_nugget_id ? {
      question: questions.primary.question,
      target_nugget_id: questions.primary.target_nugget_id,
      gap_type: questions.primary.gap_type,
      why_this_next: questions.why_primary,
    } : null,
    alternate_paths: questions.alternates.filter(a => a.target_nugget_id),
    graph_nodes: graphNodes,
    graph_edges: graphEdges,
  }, 200, origin);
}

async function handleGetGraphView(
  supabase: ReturnType<typeof createClient>,
  sessionId: string,
  origin: string,
): Promise<Response> {
  if (!sessionId) {
    return errorResponse("session_id is required", 400, origin);
  }

  const { data: nodes, error: nodesError } = await supabase
    .from("nodes")
    .select(`
      id,
      node_type,
      title,
      summary,
      nuggets (score)
    `)
    .eq("session_id", sessionId)
    .order("created_at", { ascending: false })
    .limit(20);

  if (nodesError) {
    return errorResponse(`Failed to fetch nodes: ${nodesError.message}`, 500, origin);
  }

  const { data: edges, error: edgesError } = await supabase
    .from("edges")
    .select("id, source_id, target_id, edge_type")
    .eq("session_id", sessionId);

  if (edgesError) {
    return errorResponse(`Failed to fetch edges: ${edgesError.message}`, 500, origin);
  }

  return jsonResponse({
    nodes: (nodes || []).map((n: any) => ({
      node_id: n.id,
      node_type: n.node_type,
      title: n.title,
      summary: n.summary,
      score: n.nuggets?.[0]?.score || null,
    })),
    edges: (edges || []).map((e: any) => ({
      edge_id: e.id,
      source_id: e.source_id,
      target_id: e.target_id,
      edge_type: e.edge_type,
    })),
  }, 200, origin);
}

async function handleGetNodeDetail(
  supabase: ReturnType<typeof createClient>,
  nodeId: string,
  origin: string,
): Promise<Response> {
  if (!nodeId) {
    return errorResponse("node_id is required", 400, origin);
  }

  const { data: node, error: nodeError } = await supabase
    .from("nodes")
    .select(`
      id,
      node_type,
      title,
      summary,
      nuggets (
        id,
        score,
        dimension_scores,
        missing_fields,
        next_questions,
        user_feedback
      ),
      provenance (
        source_type,
        source_id,
        created_at,
        confidence
      )
    `)
    .eq("id", nodeId)
    .single();

  if (nodeError) {
    return errorResponse("Node not found", 404, origin);
  }

  const nugget = node.nuggets?.[0];
  return jsonResponse({
    node_id: node.id,
    node_type: node.node_type,
    title: node.title,
    summary: node.summary,
    provenance: (node.provenance || []).map((p: any) => ({
      source_type: p.source_type,
      source_id: p.source_id,
      timestamp: p.created_at,
      confidence: p.confidence,
    })),
    nugget: nugget ? {
      nugget_id: nugget.id,
      score: nugget.score,
      dimension_scores: nugget.dimension_scores,
      missing_fields: nugget.missing_fields || [],
      next_questions: nugget.next_questions || [],
      user_feedback: nugget.user_feedback,
    } : null,
  }, 200, origin);
}

async function handleNuggetFeedback(
  supabase: ReturnType<typeof createClient>,
  nuggetId: string,
  body: NuggetFeedbackRequest,
  origin: string,
): Promise<Response> {
  if (!nuggetId) {
    return errorResponse("nugget_id is required", 400, origin);
  }

  if (!body.feedback || !["up", "down"].includes(body.feedback)) {
    return errorResponse("feedback must be 'up' or 'down'", 400, origin);
  }

  // Get current nugget
  const { data: nugget, error: fetchError } = await supabase
    .from("nuggets")
    .select("id, score, user_feedback")
    .eq("id", nuggetId)
    .single();

  if (fetchError) {
    return errorResponse("Nugget not found", 404, origin);
  }

  // Calculate new score
  let newScore = nugget.score;
  const UPVOTE_BOOST = 5;

  if (body.feedback === "up" && nugget.user_feedback !== "up") {
    newScore = Math.min(100, nugget.score + UPVOTE_BOOST);
  } else if (body.feedback === "down" && nugget.user_feedback === "up") {
    newScore = Math.max(0, nugget.score - UPVOTE_BOOST);
  }

  // Update nugget
  const { error: updateError } = await supabase
    .from("nuggets")
    .update({
      user_feedback: body.feedback,
      score: newScore,
    })
    .eq("id", nuggetId);

  if (updateError) {
    return errorResponse(`Failed to update feedback: ${updateError.message}`, 500, origin);
  }

  const message = body.feedback === "up"
    ? "Nugget approved. It will be prioritized in future suggestions."
    : "Nugget rejected. It will be excluded from future suggestions.";

  return jsonResponse({
    nugget_id: nuggetId,
    user_feedback: body.feedback,
    message,
  }, 200, origin);
}

async function handleNodeEdit(
  supabase: ReturnType<typeof createClient>,
  nodeId: string,
  body: NodeEditRequest,
  origin: string,
): Promise<Response> {
  if (!nodeId) {
    return errorResponse("node_id is required", 400, origin);
  }

  if (!body.title && !body.summary) {
    return errorResponse("At least one of 'title' or 'summary' must be provided", 400, origin);
  }

  // Build update object
  const nodeUpdate: Record<string, string> = {};
  const nuggetUpdate: Record<string, string> = {};
  const updatedFields: string[] = [];

  if (body.title) {
    nodeUpdate.title = body.title;
    nuggetUpdate.title = body.title;
    updatedFields.push("title");
  }
  if (body.summary) {
    nodeUpdate.summary = body.summary;
    nuggetUpdate.short_summary = body.summary.slice(0, 200);
    updatedFields.push("summary");
  }

  // Update node
  const { data: node, error: nodeError } = await supabase
    .from("nodes")
    .update(nodeUpdate)
    .eq("id", nodeId)
    .select("id, title, summary")
    .single();

  if (nodeError) {
    return errorResponse("Node not found", 404, origin);
  }

  // Update associated nugget if exists
  if (Object.keys(nuggetUpdate).length > 0) {
    await supabase
      .from("nuggets")
      .update(nuggetUpdate)
      .eq("node_id", nodeId);
  }

  return jsonResponse({
    node_id: node.id,
    title: node.title,
    summary: node.summary,
    message: `Node updated: ${updatedFields.join(", ")} changed.`,
  }, 200, origin);
}

async function handleUpload(
  supabase: ReturnType<typeof createClient>,
  body: UploadRequest,
  origin: string,
): Promise<Response> {
  // P0 minimal: accept metadata only
  if (!body.session_id || !body.filename) {
    return errorResponse("session_id and filename are required", 400, origin);
  }

  // Store document metadata (actual file would go to Storage)
  const { data: doc, error } = await supabase
    .from("documents")
    .insert({
      session_id: body.session_id,
      filename: body.filename,
      content_type: body.content_type || "application/octet-stream",
      storage_path: `uploads/${body.session_id}/${body.filename}`,
      size_bytes: body.size_bytes || 0,
    })
    .select("id, filename, size_bytes")
    .single();

  if (error) {
    return errorResponse(`Failed to store document: ${error.message}`, 500, origin);
  }

  return jsonResponse({
    document_id: doc.id,
    filename: doc.filename,
    size_bytes: doc.size_bytes,
    message: "Document metadata stored. File upload to storage pending implementation.",
  }, 200, origin);
}

// --- Main Handler ---

serve(async (req: Request) => {
  const origin = req.headers.get("origin") || "";
  const url = new URL(req.url);
  const path = url.pathname.replace("/api", "").replace("/functions/v1/api", "");
  const method = req.method;

  // Handle CORS preflight
  if (method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: corsHeaders(origin),
    });
  }

  // Create Supabase client
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

  try {
    // Health check
    if (path === "/health" || path === "") {
      return jsonResponse({
        status: "ok",
        timestamp: new Date().toISOString(),
      }, 200, origin);
    }

    // POST /chat_turn
    if (path === "/chat_turn" && method === "POST") {
      const body = await req.json();
      return handleChatTurn(supabase, body, origin);
    }

    // GET /graph_view
    if (path === "/graph_view" && method === "GET") {
      const sessionId = url.searchParams.get("session_id") || "";
      return handleGetGraphView(supabase, sessionId, origin);
    }

    // GET /node/:id
    const nodeMatch = path.match(/^\/node\/([a-f0-9-]+)$/);
    if (nodeMatch && method === "GET") {
      return handleGetNodeDetail(supabase, nodeMatch[1], origin);
    }

    // PATCH /node/:id
    if (nodeMatch && method === "PATCH") {
      const body = await req.json();
      return handleNodeEdit(supabase, nodeMatch[1], body, origin);
    }

    // POST /nugget/:id/feedback
    const feedbackMatch = path.match(/^\/nugget\/([a-f0-9-]+)\/feedback$/);
    if (feedbackMatch && method === "POST") {
      const body = await req.json();
      return handleNuggetFeedback(supabase, feedbackMatch[1], body, origin);
    }

    // POST /upload
    if (path === "/upload" && method === "POST") {
      const body = await req.json();
      return handleUpload(supabase, body, origin);
    }

    // 404 for unknown routes
    return errorResponse(`Not found: ${method} ${path}`, 404, origin);

  } catch (error) {
    console.error("Request error:", error);
    return errorResponse(
      error instanceof Error ? error.message : "Internal server error",
      500,
      origin,
    );
  }
});

/**
 * Sponge API Client
 * Connects frontend to the Supabase Edge Function API
 */

// API base URL from environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:54321/functions/v1/api';

// --- Types ---

export interface DimensionScores {
  specificity: number;
  novelty: number;
  authority: number;
  actionability: number;
  story_energy: number;
  audience_resonance: number;
}

export interface CapturedNugget {
  nugget_id: string;
  node_id: string;
  title: string;
  nugget_type: string;
  score: number;
  is_new: boolean;
  user_feedback: 'up' | 'down' | null;
  dimension_scores: DimensionScores | null;
}

export interface NextQuestion {
  question: string;
  target_nugget_id: string;
  gap_type: string;
  why_this_next: string;
}

export interface AlternatePath {
  question: string;
  target_nugget_id: string;
  gap_type: string;
}

export interface GraphNode {
  node_id: string;
  node_type: string;
  title: string;
  summary: string;
  score: number | null;
}

export interface GraphEdge {
  edge_id: string;
  source_id: string;
  target_id: string;
  edge_type: string;
}

export interface ChatTurnResponse {
  turn_id: string;
  session_id: string;
  captured_nuggets: CapturedNugget[];
  graph_update_summary: string;
  next_question: NextQuestion | null;
  alternate_paths: AlternatePath[];
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
}

export interface ExtractionFailureResponse {
  turn_id: string;
  session_id: string;
  extraction_failed: true;
  failure_reason: string;
  recovery_question: string;
  captured_nuggets: [];
  graph_update_summary: string;
}

export interface GraphViewResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface NodeDetailResponse {
  node_id: string;
  node_type: string;
  title: string;
  summary: string;
  provenance: Array<{
    source_type: string;
    source_id: string;
    timestamp: string;
    confidence: string;
  }>;
  nugget: {
    nugget_id: string;
    score: number;
    dimension_scores: DimensionScores | null;
    missing_fields: string[];
    next_questions: string[];
    user_feedback: 'up' | 'down' | null;
  } | null;
}

export interface NuggetFeedbackResponse {
  nugget_id: string;
  user_feedback: 'up' | 'down';
  message: string;
}

export interface NodeEditResponse {
  node_id: string;
  title: string;
  summary: string;
  message: string;
}

// --- API Client ---

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new ApiError(response.status, data.error || 'Request failed');
  }

  return data as T;
}

// --- API Methods ---

/**
 * Send a chat message and get extracted nuggets
 */
export async function sendChatTurn(
  message: string,
  sessionId?: string
): Promise<ChatTurnResponse | ExtractionFailureResponse> {
  return request<ChatTurnResponse | ExtractionFailureResponse>('/chat_turn', {
    method: 'POST',
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });
}

/**
 * Get the knowledge graph for a session
 */
export async function getGraphView(sessionId: string): Promise<GraphViewResponse> {
  return request<GraphViewResponse>(`/graph_view?session_id=${sessionId}`);
}

/**
 * Get details for a specific node
 */
export async function getNodeDetail(nodeId: string): Promise<NodeDetailResponse> {
  return request<NodeDetailResponse>(`/node/${nodeId}`);
}

/**
 * Submit feedback (thumbs up/down) on a nugget
 */
export async function submitNuggetFeedback(
  nuggetId: string,
  feedback: 'up' | 'down'
): Promise<NuggetFeedbackResponse> {
  return request<NuggetFeedbackResponse>(`/nugget/${nuggetId}/feedback`, {
    method: 'POST',
    body: JSON.stringify({ feedback }),
  });
}

/**
 * Edit a node's title and/or summary
 */
export async function editNode(
  nodeId: string,
  updates: { title?: string; summary?: string }
): Promise<NodeEditResponse> {
  return request<NodeEditResponse>(`/node/${nodeId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<{ status: string; timestamp: string }> {
  return request<{ status: string; timestamp: string }>('/health');
}

// --- Helper to check if response is an extraction failure ---

export function isExtractionFailure(
  response: ChatTurnResponse | ExtractionFailureResponse
): response is ExtractionFailureResponse {
  return 'extraction_failed' in response && response.extraction_failed === true;
}

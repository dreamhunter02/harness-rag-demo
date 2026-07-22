export type SystemId = "harness1" | "gpt4o";
export type RunMode = "live" | "replay";
export type RunStatus = "idle" | "queued" | "running" | "completed" | "error" | "cancelled";

export interface Question {
  id: string;
  label: string;
  query: string;
  benchmark: string;
  reference_answer?: string | null;
  gold_document_ids: string[];
}

export interface DemoEvent {
  run_id: string;
  sequence: number;
  timestamp: string;
  type: "status" | "tool_action" | "observation" | "state_snapshot" | "metrics" | "result" | "error";
  phase: string;
  payload: Record<string, unknown>;
}

export interface ActionStep {
  turn: number;
  tool: string;
  parameters: Record<string, unknown>;
  summary?: string;
  timestamp: string;
}

export interface HarnessSnapshot {
  externalized?: boolean;
  message?: string;
  candidate_pool?: Array<{ id: string; snippet?: string }>;
  curated_set?: Array<{ id: string; importance?: string }>;
  evidence_graph?: Array<{ entity: string; document_ids: string[] }>;
  verification?: Array<{ claim: string; status: string; document_ids?: string[] }>;
  compression?: { latest_summary?: string; deduplicated?: number };
  budget_render?: { used_tokens: number; limit_tokens: number };
  turn?: number;
  retrieved_document_count?: number;
}

export interface Metrics {
  total_seconds: number;
  time_to_first_action_seconds?: number | null;
  model_inference_seconds: number;
  retrieval_seconds: number;
  prompt_tokens: number;
  completion_tokens: number;
  completion_tokens_per_second?: number | null;
  action_count: number;
  estimated_cost_usd: number;
  cost_basis: string;
}

export interface ResultPayload {
  answer?: string;
  reference_answer?: string | null;
  answer_kind?: string;
  disclosure?: string;
  curated_document_ids?: string[];
  retrieved_document_ids?: string[];
  candidate_count?: number;
  recall?: number | null;
  precision?: number | null;
}

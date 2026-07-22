import type { Metrics, ResultPayload } from "../types";

export function MetricsStrip({ result, metrics }: { result: ResultPayload | null; metrics: Metrics | null }) {
  return (
    <section className="metrics-strip" aria-label="Run result and performance">
      <div className="result-cell">
        <span className="metric-label">RESULT</span>
        <strong>{result?.answer ?? "Waiting for a completed run."}</strong>
        <small>{result?.disclosure ?? "Live measurements appear here when the run completes."}</small>
      </div>
      <Metric label="TOTAL LATENCY" value={formatSeconds(metrics?.total_seconds)} note="end to end" />
      <Metric label="FIRST ACTION" value={formatSeconds(metrics?.time_to_first_action_seconds)} note="completed action" />
      <Metric label="MODEL / RETRIEVAL" value={metrics ? `${metrics.model_inference_seconds.toFixed(1)}s / ${metrics.retrieval_seconds.toFixed(1)}s` : "—"} note="measured split" />
      <Metric label="TOKENS IN / OUT" value={metrics ? `${metrics.prompt_tokens.toLocaleString()} / ${metrics.completion_tokens.toLocaleString()}` : "—"} note="provider usage" />
      <Metric label="OUTPUT TOKENS / SEC" value={metrics?.completion_tokens_per_second?.toFixed(1) ?? "—"} note="model inference" />
      <Metric label="EST. RUN COST" value={metrics ? `$${metrics.estimated_cost_usd.toFixed(4)}` : "—"} note={metrics?.cost_basis ?? "estimated"} />
    </section>
  );
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return <div className="metric-cell"><span className="metric-label">{label}</span><strong>{value}</strong><small title={note}>{note}</small></div>;
}

function formatSeconds(value?: number | null): string {
  return value === undefined || value === null ? "—" : `${value.toFixed(2)}s`;
}

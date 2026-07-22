import type { ActionStep } from "../types";

export function ActionTrajectory({ actions, running }: { actions: ActionStep[]; running: boolean }) {
  return (
    <section className="workspace-panel trajectory-panel" aria-labelledby="trajectory-title">
      <h2 id="trajectory-title">ACTION TRAJECTORY</h2>
      <div className="trajectory" aria-live="polite">
        {actions.length === 0 ? (
          <div className="empty-state">
            <span className="empty-line" />
            Select a question and run a system to watch each external action.
          </div>
        ) : (
          actions.map((action, index) => (
            <article
              className={`trajectory-step ${running && index === actions.length - 1 ? "active" : "complete"}`}
              key={`${action.turn}-${index}-${action.tool}`}
            >
              <span className="step-node" aria-hidden="true" />
              <div className="step-copy">
                <div className="step-heading">
                  <span>T{action.turn}</span>
                  <strong>{action.tool}</strong>
                  <time>{new Date(action.timestamp).toLocaleTimeString([], { minute: "2-digit", second: "2-digit" })}</time>
                </div>
                <p>{action.summary ?? summarizeParameters(action.parameters)}</p>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}

function summarizeParameters(parameters: Record<string, unknown>): string {
  const query = parameters.query ?? parameters.pattern ?? parameters.doc_id ?? parameters.claim;
  if (query) return String(query);
  const ids = parameters.add_ids ?? parameters.doc_ids;
  if (Array.isArray(ids)) return `${ids.length} document${ids.length === 1 ? "" : "s"}`;
  return "Harness state updated";
}

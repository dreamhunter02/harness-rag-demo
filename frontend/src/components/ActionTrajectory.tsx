import { useEffect, useRef } from "react";
import type { ActionStep } from "../types";

export function ActionTrajectory({
  actions,
  running,
  selectedTurn,
}: {
  actions: ActionStep[];
  running: boolean;
  selectedTurn?: number;
}) {
  const trajectoryRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!running) return;
    const trajectory = trajectoryRef.current;
    if (!trajectory) return;
    if (typeof trajectory.scrollTo === "function") {
      trajectory.scrollTo({ top: trajectory.scrollHeight, behavior: "smooth" });
    } else {
      trajectory.scrollTop = trajectory.scrollHeight;
    }
  }, [actions, running]);

  useEffect(() => {
    if (selectedTurn === undefined) return;
    const trajectory = trajectoryRef.current;
    const selected = trajectory?.querySelector<HTMLElement>(`[data-turn="${selectedTurn}"]`);
    if (!trajectory || !selected) return;
    trajectory.scrollTo({
      top: selected.offsetTop - trajectory.clientHeight / 2 + selected.clientHeight / 2,
      behavior: "smooth",
    });
  }, [selectedTurn]);

  return (
    <section className="workspace-panel trajectory-panel" aria-labelledby="trajectory-title">
      <h2 id="trajectory-title">ACTION TRAJECTORY</h2>
      <div className="trajectory" aria-live="polite" ref={trajectoryRef} tabIndex={0}>
        {actions.length === 0 ? (
          <div className="empty-state">
            <span className="empty-line" />
            Select a question and run a system to watch each external action.
          </div>
        ) : (
          actions.map((action, index) => (
            <article
              className={`trajectory-step ${action.turn === selectedTurn ? "active" : "complete"}`}
              data-turn={action.turn}
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

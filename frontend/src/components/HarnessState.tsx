import type { HarnessSnapshot, SystemId } from "../types";

type HarnessStateProps = {
  snapshot: HarnessSnapshot;
  system: SystemId;
  onPrevious?: () => void;
  onNext?: () => void;
  canGoPrevious?: boolean;
  canGoNext?: boolean;
  viewingHistory?: boolean;
};

export function HarnessState({
  snapshot,
  system,
  onPrevious,
  onNext,
  canGoPrevious = false,
  canGoNext = false,
  viewingHistory = false,
}: HarnessStateProps) {
  const inactive = system === "gpt4o" || snapshot.externalized === false;
  return (
    <section className={`workspace-panel state-panel ${inactive ? "internal-state" : ""}`} aria-labelledby="state-title">
      <div className="panel-title-row">
        <h2 id="state-title">HARNESS STATE</h2>
        {!inactive ? (
          <div className="turn-navigation" aria-label="Harness state turn navigation">
            <button type="button" onClick={onPrevious} disabled={!canGoPrevious} aria-label="Previous turn">&lt;</button>
            <span>{viewingHistory ? "history" : "live"} · turn {snapshot.turn ?? 0}</span>
            <button type="button" onClick={onNext} disabled={!canGoNext} aria-label="Next turn">&gt;</button>
          </div>
        ) : null}
      </div>
      {inactive ? (
        <div className="internal-message">
          <strong>State remains inside the model context.</strong>
          <p>GPT‑4o mini uses the same search and read access without Harness‑1’s externalized working memory.</p>
          {snapshot.retrieved_document_count ? <span>{snapshot.retrieved_document_count} documents retrieved</span> : null}
        </div>
      ) : (
        <div className="state-grid" aria-live="polite">
          <StateCell title="candidate pool" active={Boolean(snapshot.candidate_pool?.length)}>
            <DocumentList items={snapshot.candidate_pool?.map((item) => item.id) ?? []} />
            <CellCount count={snapshot.candidate_pool?.length ?? 0} noun="candidate" />
          </StateCell>
          <StateCell title="curated set" active={Boolean(snapshot.curated_set?.length)} featured>
            <ul className="document-list">
              {snapshot.curated_set?.map((item) => (
                <li key={item.id}><span>{item.id}</span><em>{item.importance ?? "fair"}</em></li>
              ))}
            </ul>
            <CellCount count={snapshot.curated_set?.length ?? 0} noun="curated" />
          </StateCell>
          <StateCell title="evidence graph" active={Boolean(snapshot.evidence_graph?.length)}>
            <ul className="graph-list">
              {snapshot.evidence_graph?.map((item) => (
                <li key={item.entity}><span>{item.entity}</span><small>{item.document_ids.length} links</small></li>
              ))}
            </ul>
            <CellCount count={snapshot.evidence_graph?.length ?? 0} noun="bridge" />
          </StateCell>
          <StateCell title="verification" active={Boolean(snapshot.verification?.length)}>
            <ul className="verification-list">
              {snapshot.verification?.map((item, index) => (
                <li key={`${item.claim}-${index}`}><span className="check">✓</span>{item.claim}</li>
              ))}
            </ul>
            <CellCount count={snapshot.verification?.length ?? 0} noun="check" />
          </StateCell>
          <StateCell title="compression" active={Boolean(snapshot.compression?.latest_summary)}>
            <p className="compression-copy">{snapshot.compression?.latest_summary || "Waiting for a result summary."}</p>
            <span className="cell-foot">{snapshot.compression?.deduplicated ?? 0} duplicates removed</span>
          </StateCell>
          <StateCell title="budget render" active={Boolean(snapshot.budget_render?.used_tokens)}>
            <Budget used={snapshot.budget_render?.used_tokens ?? 0} limit={snapshot.budget_render?.limit_tokens ?? 32268} />
          </StateCell>
        </div>
      )}
    </section>
  );
}

function StateCell({ title, active, featured, children }: { title: string; active: boolean; featured?: boolean; children: React.ReactNode }) {
  return (
    <article className={`state-cell ${active ? "populated" : ""} ${featured ? "featured" : ""}`}>
      <h3>{title}</h3>
      <div className="state-cell-content" tabIndex={0}>{children}</div>
    </article>
  );
}

function DocumentList({ items }: { items: string[] }) {
  return <ul className="document-list">{items.map((item) => <li key={item}><span>{item}</span></li>)}</ul>;
}

function CellCount({ count, noun }: { count: number; noun: string }) {
  return <span className="cell-foot">{count} {noun}{count === 1 ? "" : "s"}</span>;
}

function Budget({ used, limit }: { used: number; limit: number }) {
  const percentage = Math.min(100, Math.round((used / Math.max(limit, 1)) * 100));
  return <div className="budget"><strong>{used.toLocaleString()} / {limit.toLocaleString()}</strong><div className="budget-track"><span style={{ width: `${percentage}%` }} /></div><span className="cell-foot">{percentage}% used</span></div>;
}

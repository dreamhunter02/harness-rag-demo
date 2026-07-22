import type { HarnessSnapshot, SystemId } from "../types";

export function HarnessState({ snapshot, system }: { snapshot: HarnessSnapshot; system: SystemId }) {
  const inactive = system === "gpt4o" || snapshot.externalized === false;
  return (
    <section className={`workspace-panel state-panel ${inactive ? "internal-state" : ""}`} aria-labelledby="state-title">
      <div className="panel-title-row">
        <h2 id="state-title">HARNESS STATE</h2>
        {!inactive && snapshot.turn !== undefined ? <span>turn {snapshot.turn}</span> : null}
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
            <DocumentList items={snapshot.candidate_pool?.slice(-5).map((item) => item.id) ?? []} />
            <CellCount count={snapshot.candidate_pool?.length ?? 0} noun="candidate" />
          </StateCell>
          <StateCell title="curated set" active={Boolean(snapshot.curated_set?.length)} featured>
            <ul className="document-list">
              {snapshot.curated_set?.slice(0, 5).map((item) => (
                <li key={item.id}><span>{item.id}</span><em>{item.importance ?? "fair"}</em></li>
              ))}
            </ul>
            <CellCount count={snapshot.curated_set?.length ?? 0} noun="curated" />
          </StateCell>
          <StateCell title="evidence graph" active={Boolean(snapshot.evidence_graph?.length)}>
            <ul className="graph-list">
              {snapshot.evidence_graph?.slice(0, 3).map((item) => (
                <li key={item.entity}><span>{item.entity}</span><small>{item.document_ids.length} links</small></li>
              ))}
            </ul>
            <CellCount count={snapshot.evidence_graph?.length ?? 0} noun="bridge" />
          </StateCell>
          <StateCell title="verification" active={Boolean(snapshot.verification?.length)}>
            <ul className="verification-list">
              {snapshot.verification?.slice(-3).map((item, index) => (
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
  return <article className={`state-cell ${active ? "populated" : ""} ${featured ? "featured" : ""}`}><h3>{title}</h3>{children}</article>;
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

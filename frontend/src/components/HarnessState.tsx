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
          <StateCell title="candidate pool" placement="candidate" active={Boolean(snapshot.candidate_pool?.length)}>
            <DocumentList items={snapshot.candidate_pool?.map((item) => item.id) ?? []} />
            <CellCount count={snapshot.candidate_pool?.length ?? 0} noun="candidate" />
          </StateCell>
          <StateCell title="evidence graph" placement="graph" active={Boolean(snapshot.evidence_graph?.length)}>
            <ul className="graph-list">
              {snapshot.evidence_graph?.map((item) => (
                <li key={item.entity}>
                  <div className="graph-entity"><strong>{item.entity}</strong><small>{item.document_ids.length} link{item.document_ids.length === 1 ? "" : "s"}</small></div>
                  <div className="graph-documents" aria-label={`Documents linked to ${item.entity}`}>
                    {item.document_ids.map((documentId) => <span key={documentId}>DOC {documentId}</span>)}
                  </div>
                </li>
              ))}
            </ul>
            <CellCount count={snapshot.evidence_graph?.length ?? 0} noun="entity" />
          </StateCell>
          <StateCell title="curated set" placement="curated" active={Boolean(snapshot.curated_set?.length)} featured>
            <ul className="document-list">
              {snapshot.curated_set?.map((item) => (
                <li key={item.id}><span>{item.id}</span><em>{item.importance ?? "fair"}</em></li>
              ))}
            </ul>
            <CellCount count={snapshot.curated_set?.length ?? 0} noun="curated" />
          </StateCell>
          <StateCell title="verification" placement="verification" active={Boolean(snapshot.verification?.length)}>
            <ul className="verification-list">
              {snapshot.verification?.map((item, index) => (
                <li key={`${item.claim}-${index}`}><span className="check">✓</span>{item.claim}</li>
              ))}
            </ul>
            <CellCount count={snapshot.verification?.length ?? 0} noun="check" />
          </StateCell>
          <StateCell title="compression" placement="compression" active={Boolean(snapshot.compression?.latest_summary)}>
            <p className="compression-copy">{snapshot.compression?.latest_summary || "Waiting for a result summary."}</p>
            <span className="cell-foot">{snapshot.compression?.deduplicated ?? 0} duplicates removed</span>
          </StateCell>
        </div>
      )}
    </section>
  );
}

function StateCell({ title, placement, active, featured, children }: { title: string; placement: string; active: boolean; featured?: boolean; children: React.ReactNode }) {
  return (
    <article className={`state-cell state-${placement} ${active ? "populated" : ""} ${featured ? "featured" : ""}`}>
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

import { useEffect, useRef, useState } from "react";
import { cancelRun, createRun, getHealth, getQuestions } from "./api";
import { ActionTrajectory } from "./components/ActionTrajectory";
import { HarnessState } from "./components/HarnessState";
import { MetricsStrip } from "./components/MetricsStrip";
import type {
  ActionStep,
  DemoEvent,
  HarnessSnapshot,
  Metrics,
  Question,
  ResultPayload,
  RunMode,
  RunStatus,
  SystemId,
} from "./types";

const EVENT_NAMES = ["status", "tool_action", "observation", "state_snapshot", "metrics", "result"] as const;

export default function App() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionId, setQuestionId] = useState("");
  const [system, setSystem] = useState<SystemId>("harness1");
  const [status, setStatus] = useState<RunStatus>("idle");
  const [actions, setActions] = useState<ActionStep[]>([]);
  const [snapshot, setSnapshot] = useState<HarnessSnapshot>({});
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [result, setResult] = useState<ResultPayload | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [replayAvailable, setReplayAvailable] = useState(false);
  const [mode, setMode] = useState<RunMode>("live");
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const sourceRef = useRef<EventSource | null>(null);
  const seenSequences = useRef(new Set<number>());

  useEffect(() => {
    getQuestions().then((items) => {
      setQuestions(items);
      setQuestionId(items[0]?.id ?? "");
    }).catch((cause) => setError(String(cause)));
    getHealth().then(setHealth).catch(() => setHealth(null));
    return () => sourceRef.current?.close();
  }, []);

  const selectedQuestion = questions.find((question) => question.id === questionId);
  const running = status === "queued" || status === "running";

  function resetRun(nextMode: RunMode) {
    sourceRef.current?.close();
    seenSequences.current.clear();
    setActions([]);
    setSnapshot(system === "gpt4o" ? { externalized: false, message: "State remains inside the model context." } : {});
    setMetrics(null);
    setResult(null);
    setError(null);
    setReplayAvailable(false);
    setMode(nextMode);
  }

  async function start(nextMode: RunMode = "live") {
    if (!questionId) return;
    resetRun(nextMode);
    setStatus("queued");
    try {
      const record = await createRun(questionId, system, nextMode);
      setRunId(record.id);
      connect(record.id);
    } catch (cause) {
      setStatus("error");
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  }

  function connect(id: string) {
    const source = new EventSource(`/api/runs/${id}/events`);
    sourceRef.current = source;
    EVENT_NAMES.forEach((name) => source.addEventListener(name, consumeEvent));
    source.addEventListener("error", (event) => {
      // `error` is both a valid named demo event and EventSource's transport error.
      if (event instanceof MessageEvent && typeof event.data === "string") consumeEvent(event);
      else setError((current) => current ?? "Event stream disconnected; attempting to reconnect.");
    });
  }

  function consumeEvent(message: MessageEvent<string>) {
    const event = JSON.parse(message.data) as DemoEvent;
    if (seenSequences.current.has(event.sequence)) return;
    seenSequences.current.add(event.sequence);
    if (event.type === "status") {
      const next = event.payload.status as RunStatus;
      setStatus(next);
      if (["completed", "error", "cancelled"].includes(next)) sourceRef.current?.close();
    } else if (event.type === "tool_action") {
      const turn = Number(event.payload.turn ?? 0);
      const calls = (event.payload.calls ?? []) as Array<{ tool: string; parameters: Record<string, unknown> }>;
      const timestamp = event.timestamp;
      setActions((current) => [...current, ...calls.map((call) => ({ turn, ...call, timestamp }))]);
    } else if (event.type === "observation") {
      const summaries = event.payload.summaries as string[] | undefined;
      setActions((current) => current.map((item, index) => (
        index === current.length - 1 && summaries?.[0] ? { ...item, summary: summaries[0] } : item
      )));
    } else if (event.type === "state_snapshot") {
      setSnapshot(event.payload as HarnessSnapshot);
    } else if (event.type === "metrics") {
      setMetrics(event.payload as unknown as Metrics);
    } else if (event.type === "result") {
      setResult(event.payload as ResultPayload);
    } else if (event.type === "error") {
      setStatus("error");
      setError(String(event.payload.message ?? "Run failed"));
      setReplayAvailable(Boolean(event.payload.replay_available));
    }
  }

  async function stop() {
    if (!runId) return;
    await cancelRun(runId);
    setStatus("cancelled");
    sourceRef.current?.close();
  }

  const healthLabel = health?.status === "ready" ? "All systems ready" : health ? "Setup incomplete" : "Backend unavailable";

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="title-lockup"><span className="green-rule" /><h1>Harness-1 · Live Search Demo</h1></div>
        <div className={`connection-status ${health?.status === "ready" ? "ready" : "degraded"}`}>
          <span className="status-dot" />{healthLabel}
        </div>
      </header>

      {mode === "replay" ? <div className="replay-banner">DEMO REPLAY · NOT A LIVE MEASUREMENT</div> : null}

      <section className="run-controls" aria-label="Run controls">
        <label>
          <span>QUESTION</span>
          <select value={questionId} onChange={(event) => setQuestionId(event.target.value)} disabled={running}>
            {questions.map((question, index) => <option value={question.id} key={question.id}>BrowseComp+ · Question {index + 1} · {question.label}</option>)}
          </select>
        </label>
        <label>
          <span>SYSTEM</span>
          <select value={system} onChange={(event) => setSystem(event.target.value as SystemId)} disabled={running}>
            <option value="harness1">Harness-1 20B · Brev</option>
            <option value="gpt4o">GPT‑4o · OpenAI</option>
          </select>
        </label>
        {running ? (
          <button className="run-button running" onClick={stop}><span className="spinner" />CANCEL RUN</button>
        ) : (
          <button className="run-button" onClick={() => start("live")} disabled={!questionId}>RUN</button>
        )}
      </section>

      <div className="query-line"><span>{selectedQuestion?.benchmark ?? "BrowseComp+ Demo Slice"}</span><p>{selectedQuestion?.query}</p></div>

      {error ? (
        <aside className="error-bar" role="alert">
          <span>{error}</span>
          {replayAvailable ? <button onClick={() => start("replay")}>REPLAY LAST SUCCESSFUL RUN</button> : null}
        </aside>
      ) : null}

      <section className="workspace">
        <ActionTrajectory actions={actions} running={running} />
        <HarnessState snapshot={snapshot} system={system} />
      </section>

      <MetricsStrip result={result} metrics={metrics} />
      <footer><span>{status.toUpperCase()}</span><span>Results use a disclosed curated demo slice · Costs are estimates</span></footer>
    </main>
  );
}

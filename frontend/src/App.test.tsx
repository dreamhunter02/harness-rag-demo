import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  listeners = new Map<string, Array<(event: Event) => void>>();
  constructor(public url: string) { FakeEventSource.instances.push(this); }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
    const callback = typeof listener === "function" ? listener : (event: Event) => listener.handleEvent(event);
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), callback]);
  }
  close() {}
  emit(type: string, payload: Record<string, unknown>) {
    const event = new MessageEvent(type, { data: JSON.stringify(payload) });
    this.listeners.get(type)?.forEach((listener) => listener(event));
  }
}

const question = {
  id: "bcplus-100",
  label: "Dream above a desert town",
  query: "Which newspaper published the article?",
  benchmark: "BrowseComp+ Demo Slice",
  gold_document_ids: [],
};

describe("App", () => {
  beforeEach(() => {
    FakeEventSource.instances = [];
    vi.stubGlobal("EventSource", FakeEventSource);
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/questions")) return new Response(JSON.stringify([question]));
      if (url.endsWith("/api/health")) return new Response(JSON.stringify({ status: "ready" }));
      if (url.endsWith("/api/runs")) {
        const body = JSON.parse(String(init?.body));
        return new Response(JSON.stringify({ id: `run-${body.mode}` }), { status: 202 });
      }
      return new Response("{}", { status: 200 });
    }));
  });

  afterEach(() => vi.unstubAllGlobals());

  it("offers both systems and visibly labels replay recovery", async () => {
    render(<App />);
    expect(await screen.findByRole("option", { name: /Dream above a desert town/ })).toBeInTheDocument();
    expect(screen.getByText("Which newspaper published the article?")).toBeVisible();
    fireEvent.click(screen.getByText("FULL QUESTION"));
    expect(screen.getByText("Which newspaper published the article?")).not.toBeVisible();
    fireEvent.click(screen.getByText("FULL QUESTION"));
    fireEvent.change(screen.getAllByRole("combobox")[1], { target: { value: "gpt4o" } });
    expect(screen.getByRole("option", { name: /GPT‑4o/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "RUN" }));
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    FakeEventSource.instances[0].emit("error", {
      run_id: "run-live",
      sequence: 2,
      timestamp: new Date().toISOString(),
      type: "error",
      phase: "error",
      payload: { message: "provider unavailable", replay_available: true },
    });

    const replay = await screen.findByRole("button", { name: "REPLAY LAST SUCCESSFUL RUN" });
    fireEvent.click(replay);
    expect(await screen.findByText("DEMO REPLAY · NOT A LIVE MEASUREMENT")).toBeInTheDocument();
  });
});

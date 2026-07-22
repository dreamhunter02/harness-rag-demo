import { render, screen } from "@testing-library/react";
import { MetricsStrip } from "./MetricsStrip";

describe("MetricsStrip", () => {
  it("separates end-to-end, model, retrieval, throughput, and estimated cost", () => {
    render(<MetricsStrip result={{ answer: "Phoenix New Times" }} metrics={{
      total_seconds: 18.42,
      time_to_first_action_seconds: 1.23,
      model_inference_seconds: 12,
      retrieval_seconds: 4.2,
      prompt_tokens: 8000,
      completion_tokens: 742,
      completion_tokens_per_second: 61.8,
      action_count: 5,
      estimated_cost_usd: 0.021,
      cost_basis: "estimate",
    }} />);
    expect(screen.getByText("Phoenix New Times")).toBeInTheDocument();
    expect(screen.getByText("MODEL / RETRIEVAL")).toBeInTheDocument();
    expect(screen.getByText("OUTPUT TOKENS / SEC")).toBeInTheDocument();
    expect(screen.getByText("$0.0210")).toBeInTheDocument();
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { HarnessState } from "./HarnessState";

describe("HarnessState", () => {
  it("makes the GPT-4o architecture difference explicit", () => {
    render(<HarnessState system="gpt4o" snapshot={{ externalized: false }} />);
    expect(screen.getByText("State remains inside the model context.")).toBeInTheDocument();
  });

  it("renders the five presentation state contracts without budget render", () => {
    render(<HarnessState system="harness1" snapshot={{ turn: 2, evidence_graph: [{ entity: "Hatpin", document_ids: ["34889", "73556"] }] }} />);
    for (const label of ["candidate pool", "evidence graph", "curated set", "verification", "compression"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.queryByText("budget render")).not.toBeInTheDocument();
    expect(screen.getByText("DOC 34889")).toBeInTheDocument();
    expect(screen.getByText("DOC 73556")).toBeInTheDocument();
  });

  it("offers previous and next turn navigation", () => {
    const onPrevious = vi.fn();
    const onNext = vi.fn();
    render(
      <HarnessState
        system="harness1"
        snapshot={{ turn: 4 }}
        onPrevious={onPrevious}
        onNext={onNext}
        canGoPrevious
        canGoNext
        viewingHistory
      />,
    );

    expect(screen.getByText("history · turn 4")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Previous turn" }));
    fireEvent.click(screen.getByRole("button", { name: "Next turn" }));
    expect(onPrevious).toHaveBeenCalledOnce();
    expect(onNext).toHaveBeenCalledOnce();
  });
});

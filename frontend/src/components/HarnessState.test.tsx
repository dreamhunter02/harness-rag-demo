import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { HarnessState } from "./HarnessState";

describe("HarnessState", () => {
  it("makes the GPT-4o architecture difference explicit", () => {
    render(<HarnessState system="gpt4o" snapshot={{ externalized: false }} />);
    expect(screen.getByText("State remains inside the model context.")).toBeInTheDocument();
  });

  it("renders all six externalized state contracts", () => {
    render(<HarnessState system="harness1" snapshot={{ turn: 2 }} />);
    for (const label of ["candidate pool", "curated set", "evidence graph", "verification", "compression", "budget render"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
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

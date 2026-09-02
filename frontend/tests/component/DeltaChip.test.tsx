import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DeltaChip } from "@/components/badges/DeltaChip";

// Direction convention (design doc, D-004): in a price index, a RISING fare is the
// adverse direction. These tests lock that convention in so it can never silently flip
// back to the "green = up" stock-market default during a refactor.
describe("DeltaChip", () => {
  it("renders a rising fare with the adverse (up) colour class", () => {
    render(<DeltaChip value={7.4} />);
    const chip = screen.getByText(/\+7\.4%/);
    expect(chip.closest("span")).toHaveClass("text-price-up");
  });

  it("renders a falling fare with the benign (down) colour class", () => {
    render(<DeltaChip value={-3.2} />);
    const chip = screen.getByText(/-3\.2%/);
    expect(chip.closest("span")).toHaveClass("text-price-down");
  });

  it("renders a flat change without a directional sign", () => {
    render(<DeltaChip value={0.1} />);
    expect(screen.getByText("–")).toBeInTheDocument();
  });

  it("renders an em dash for a null value rather than crashing", () => {
    render(<DeltaChip value={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("shows the comparison basis alongside the value", () => {
    render(<DeltaChip value={5} basis="YoY" />);
    expect(screen.getByText("YoY")).toBeInTheDocument();
  });
});

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { PanelShell } from "@/components/panels/PanelShell";

// PanelShell requires `source` as a mandatory prop at the type level (design doc D2,
// implementation D-034). This test checks the runtime behaviour that backs that
// guarantee: the footer always renders the source string.
describe("PanelShell", () => {
  it("always renders its source attribution in the footer", () => {
    render(
      <PanelShell title="Test Panel" source="fare_observations" count={42}>
        <p>content</p>
      </PanelShell>,
    );
    expect(screen.getByText(/Source: fare_observations/)).toBeInTheDocument();
    expect(screen.getByText(/n=42/)).toBeInTheDocument();
  });

  it("renders the quality threshold when provided", () => {
    render(
      <PanelShell title="Test Panel" source="fare_observations" qualityThreshold={60}>
        <p>content</p>
      </PanelShell>,
    );
    expect(screen.getByText(/quality ≥ 60/)).toBeInTheDocument();
  });

  it("renders its title as a heading", () => {
    render(
      <PanelShell title="Airfare Index Trend" source="index_values">
        <p>content</p>
      </PanelShell>,
    );
    expect(screen.getByRole("heading", { name: "Airfare Index Trend" })).toBeInTheDocument();
  });
});

import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { DeltaChip } from "@/components/badges/DeltaChip";
import { SeverityBadge } from "@/components/badges/SeverityBadge";
import { QualityIndicator } from "@/components/badges/QualityIndicator";
import { PanelShell } from "@/components/panels/PanelShell";
import { DisclaimerBanner } from "@/components/cpi/DisclaimerBanner";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";

expect.extend(toHaveNoViolations);

// WCAG 2.1 AA spot-checks (build prompt Sec.32) on the components used on every page.
describe("accessibility", () => {
  it("KpiCard delta chip has no axe violations", async () => {
    const { container } = render(<DeltaChip value={7.4} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("SeverityBadge has no axe violations", async () => {
    const { container } = render(<SeverityBadge severity="HIGH" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("QualityIndicator has no axe violations", async () => {
    const { container } = render(<QualityIndicator score={94} band="HIGH" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("PanelShell has no axe violations", async () => {
    const { container } = render(
      <PanelShell title="Airfare Index Trend" source="index_values" count={100}>
        <p>chart content</p>
      </PanelShell>,
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it("DisclaimerBanner (role=alert) has no axe violations", async () => {
    const { container } = render(<DisclaimerBanner text="Simulation only." />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("Breadcrumbs has no axe violations and marks the current page", async () => {
    const { container, getByText } = render(
      <Breadcrumbs items={[{ label: "Home", href: "/dashboard" }, { label: "Routes", href: "/routes" }, { label: "DEL-BOM" }]} />,
    );
    expect(await axe(container)).toHaveNoViolations();
    expect(getByText("DEL-BOM")).toHaveAttribute("aria-current", "page");
  });
});

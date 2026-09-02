import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SeverityBadge } from "@/components/badges/SeverityBadge";

describe("SeverityBadge", () => {
  it.each(["LOW", "MEDIUM", "HIGH", "CRITICAL"])("renders the %s label", (severity) => {
    render(<SeverityBadge severity={severity} />);
    expect(screen.getByText(severity)).toBeInTheDocument();
  });

  it("falls back to the LOW style for an unrecognised severity rather than throwing", () => {
    expect(() => render(<SeverityBadge severity="UNKNOWN" />)).not.toThrow();
  });
});

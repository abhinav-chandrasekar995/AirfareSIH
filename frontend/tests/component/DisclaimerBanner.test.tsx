import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DisclaimerBanner } from "@/components/cpi/DisclaimerBanner";

// Build prompt Sec.15: the disclaimer must not be dismissible. There is no close
// button in the component's markup at all - this test asserts that absence directly.
describe("DisclaimerBanner", () => {
  it("renders the disclaimer text", () => {
    render(<DisclaimerBanner text="This module is a simulation." />);
    expect(screen.getByText(/This module is a simulation\./)).toBeInTheDocument();
  });

  it("renders as an alert role for assistive technology", () => {
    render(<DisclaimerBanner text="Simulation only." />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("never renders a dismiss/close button", () => {
    render(<DisclaimerBanner text="Simulation only." />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

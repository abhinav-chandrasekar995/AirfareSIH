import { describe, expect, it } from "vitest";
import { inr, pct, num, priceDirectionClass, compactNum } from "@/lib/format";

describe("format helpers", () => {
  it("inr formats with Indian digit grouping and a rupee glyph", () => {
    expect(inr(1045000)).toBe("₹10,45,000");
  });

  it("inr returns an em dash for null/undefined", () => {
    expect(inr(null)).toBe("—");
    expect(inr(undefined)).toBe("—");
  });

  it("pct signs positive values and formats negatives without a double sign", () => {
    expect(pct(7.4)).toBe("+7.4%");
    expect(pct(-3.2)).toBe("-3.2%");
  });

  it("compactNum abbreviates lakhs and crores", () => {
    expect(compactNum(240000)).toBe("2.4L");
    expect(compactNum(24000000)).toBe("2.4Cr");
  });

  it("priceDirectionClass marks a rising fare as adverse (up), not benign (down)", () => {
    // This locks the direction convention: rising price = --price-up = adverse red.
    expect(priceDirectionClass(5)).toBe("text-price-up");
    expect(priceDirectionClass(-5)).toBe("text-price-down");
    expect(priceDirectionClass(0.1)).toBe("text-price-flat");
  });

  it("num renders with the requested decimal precision", () => {
    expect(num(127.4, 1)).toBe("127.4");
    expect(num(127, 0)).toBe("127");
  });
});

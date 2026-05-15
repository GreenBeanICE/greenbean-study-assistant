import { describe, expect, it } from "vitest";
import { normalizeTitle } from "./title";

describe("normalizeTitle", () => {
  it("should trim spaces", () => {
    expect(normalizeTitle("  Cours MIAGE  ")).toBe("Cours MIAGE");
  });
});

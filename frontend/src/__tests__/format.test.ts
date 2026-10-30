import { describe, expect, it } from "vitest";
import { visibleWhitespace } from "../lib/format";
import { greeting } from "../lib/greeting";
import { AVATAR_OPTIONS } from "../store/profile";

describe("visibleWhitespace", () => {
  it("marks leading spaces", () => {
    expect(visibleWhitespace(" Jaipur")).toContain("·");
  });
});

describe("greeting", () => {
  it("morning", () => {
    const g = greeting(new Date("2026-01-01T08:00:00"));
    expect(g.text).toBe("Good Morning");
  });
});

describe("profile avatars", () => {
  it("provides exactly seven supplied avatar options", () => {
    expect(AVATAR_OPTIONS).toHaveLength(7);
    expect(new Set(AVATAR_OPTIONS.map((avatar) => avatar.src)).size).toBe(7);
  });
});

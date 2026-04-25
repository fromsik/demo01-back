import test from "node:test";
import assert from "node:assert/strict";
import { validateGoals, validateTimeBlocks } from "../src/utils/validation.js";

test("validateGoals enforces max 5", () => {
  assert.throws(() =>
    validateGoals(Array.from({ length: 6 }).map((_, i) => ({ content: `g${i + 1}` })))
  );
});

test("validateTimeBlocks rejects overlapping ranges", () => {
  assert.throws(() =>
    validateTimeBlocks([
      { startTime: "07:00", endTime: "08:00", title: "A" },
      { startTime: "07:30", endTime: "09:00", title: "B" }
    ])
  );
});

test("validateTimeBlocks allows touching ranges", () => {
  const blocks = validateTimeBlocks([
    { startTime: "07:00", endTime: "07:30", title: "A" },
    { startTime: "07:30", endTime: "09:00", title: "B" }
  ]);
  assert.equal(blocks.length, 2);
});

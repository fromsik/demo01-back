const TIME_REGEX = /^([01]\d|2[0-3]):([0-5]\d)$/;

export function toMinutes(time) {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + m;
}

export function assertTenMinuteUnit(time, fieldName) {
  if (!TIME_REGEX.test(time)) {
    throw new Error(`${fieldName} must match HH:MM`);
  }
  if (toMinutes(time) % 10 !== 0) {
    throw new Error(`${fieldName} must be in 10-minute units`);
  }
}

export function validateTimeBlocks(blocks) {
  const normalized = blocks.map((block, idx) => {
    if (!block.title || !String(block.title).trim()) {
      throw new Error(`timeBlocks[${idx}].title is required`);
    }
    assertTenMinuteUnit(block.startTime, `timeBlocks[${idx}].startTime`);
    assertTenMinuteUnit(block.endTime, `timeBlocks[${idx}].endTime`);

    const start = toMinutes(block.startTime);
    const end = toMinutes(block.endTime);

    if (start >= end) {
      throw new Error(`timeBlocks[${idx}] startTime must be before endTime`);
    }

    return {
      ...block,
      startMinutes: start,
      endMinutes: end
    };
  });

  normalized.sort((a, b) => a.startMinutes - b.startMinutes);

  for (let i = 1; i < normalized.length; i += 1) {
    if (normalized[i - 1].endMinutes > normalized[i].startMinutes) {
      throw new Error("이미 사용 중인 시간대가 있습니다. 시간을 다시 선택해주세요.");
    }
  }

  return normalized.map(({ startMinutes, endMinutes, ...rest }, index) => ({
    ...rest,
    sortOrder: index + 1
  }));
}

export function validateGoals(goals) {
  const nonEmpty = goals
    .map((goal) => ({ ...goal, content: String(goal.content || "").trim() }))
    .filter((goal) => goal.content.length > 0);

  if (nonEmpty.length < 1) {
    throw new Error("At least one goal is required");
  }
  if (nonEmpty.length > 5) {
    throw new Error("오늘의 핵심 목표는 최대 5개까지 작성할 수 있습니다.");
  }

  return nonEmpty.map((goal, idx) => ({
    ...goal,
    sortOrder: idx + 1,
    isCompleted: Boolean(goal.isCompleted)
  }));
}

export function ensurePlanDate(date) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    throw new Error("planDate must match YYYY-MM-DD");
  }
}

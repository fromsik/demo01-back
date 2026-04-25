export const store = {
  users: [],
  sessions: new Map(),
  templates: [],
  dailyPlans: [],
  sequences: {
    user: 1,
    template: 1,
    templateBlock: 1,
    dailyPlan: 1,
    dailyGoal: 1,
    dailyTimeBlock: 1
  }
};

export function nextId(key) {
  const id = store.sequences[key];
  store.sequences[key] += 1;
  return id;
}

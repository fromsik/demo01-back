import crypto from "node:crypto";
import http from "node:http";
import { URL } from "node:url";
import { store, nextId } from "./data/store.js";
import { ensurePlanDate, validateGoals, validateTimeBlocks } from "./utils/validation.js";

function sendJson(res, status, payload) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload));
}

function sendNoContent(res) {
  res.writeHead(204);
  res.end();
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  if (chunks.length === 0) return {};
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw new Error("Invalid JSON body");
  }
}

function getAuthUser(req) {
  const auth = req.headers.authorization || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : null;
  if (!token) return null;
  return { token, user: store.sessions.get(token) || null };
}

function requireAuth(req, res) {
  const auth = getAuthUser(req);
  if (!auth || !auth.user) {
    sendJson(res, 401, { message: "로그인이 필요한 기능입니다." });
    return null;
  }
  return auth;
}

function notFound(res) {
  sendJson(res, 404, { message: "not found" });
}

function methodNotAllowed(res) {
  sendJson(res, 405, { message: "method not allowed" });
}

function parseId(segment) {
  const n = Number(segment);
  return Number.isInteger(n) ? n : null;
}

function findPlanById(userId, planId) {
  return store.dailyPlans.find((plan) => plan.id === planId && plan.userId === userId);
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const path = url.pathname;
    const method = req.method;
    const parts = path.split("/").filter(Boolean);

    if (path === "/health" && method === "GET") {
      return sendJson(res, 200, { status: "ok" });
    }

    if (path === "/api/auth/google" || path === "/api/auth/kakao" || path === "/api/auth/naver") {
      if (method !== "GET") return methodNotAllowed(res);
      return sendJson(res, 200, {
        provider: parts[2],
        message: `${parts[2]} OAuth should redirect from web client.`
      });
    }

    if (path === "/api/auth/login/dev" && method === "POST") {
      const body = await readBody(req);
      const { providerType = "GOOGLE", providerUserId, email, nickname } = body;
      if (!providerUserId) return sendJson(res, 400, { message: "providerUserId is required" });

      let user = store.users.find(
        (u) => u.providerType === providerType && u.providerUserId === providerUserId
      );
      if (!user) {
        user = {
          id: nextId("user"),
          providerType,
          providerUserId,
          email: email || null,
          nickname: nickname || null,
          profileImageUrl: null,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        store.users.push(user);
      }

      const token = crypto.randomBytes(24).toString("hex");
      store.sessions.set(token, user);
      return sendJson(res, 200, { accessToken: token, user });
    }

    if (path === "/api/auth/me" && method === "GET") {
      const auth = requireAuth(req, res);
      if (!auth) return;
      return sendJson(res, 200, { user: auth.user });
    }

    if (path === "/api/auth/logout" && method === "POST") {
      const auth = requireAuth(req, res);
      if (!auth) return;
      store.sessions.delete(auth.token);
      return sendNoContent(res);
    }

    if (parts[0] === "api" && parts[1] === "templates") {
      const auth = requireAuth(req, res);
      if (!auth) return;
      const userId = auth.user.id;

      if (parts.length === 2) {
        if (method === "GET") {
          return sendJson(res, 200, store.templates.filter((t) => t.userId === userId));
        }

        if (method === "POST") {
          const body = await readBody(req);
          const { name, description = null, blocks = [] } = body;
          if (!name || !String(name).trim()) return sendJson(res, 400, { message: "name is required" });

          const validBlocks = validateTimeBlocks(blocks);
          const now = new Date().toISOString();
          const templateId = nextId("template");
          const template = {
            id: templateId,
            userId,
            name: String(name).trim(),
            description,
            isDefault: false,
            createdAt: now,
            updatedAt: now,
            blocks: validBlocks.map((block) => ({
              id: nextId("templateBlock"),
              templateId,
              startTime: block.startTime,
              endTime: block.endTime,
              title: block.title,
              memo: block.memo || null,
              sortOrder: block.sortOrder,
              createdAt: now,
              updatedAt: now
            }))
          };
          store.templates.push(template);
          return sendJson(res, 201, template);
        }

        return methodNotAllowed(res);
      }

      if (parts.length === 3) {
        const templateId = parseId(parts[2]);
        if (!templateId) return notFound(res);
        const template = store.templates.find((t) => t.id === templateId && t.userId === userId);
        if (!template) return sendJson(res, 404, { message: "template not found" });

        if (method === "GET") return sendJson(res, 200, template);
        if (method === "DELETE") {
          const idx = store.templates.findIndex((t) => t.id === templateId && t.userId === userId);
          store.templates.splice(idx, 1);
          return sendNoContent(res);
        }
        if (method === "PUT") {
          const body = await readBody(req);
          const { name, description = null, blocks = [] } = body;
          if (!name || !String(name).trim()) return sendJson(res, 400, { message: "name is required" });
          const validBlocks = validateTimeBlocks(blocks);
          const now = new Date().toISOString();
          template.name = String(name).trim();
          template.description = description;
          template.updatedAt = now;
          template.blocks = validBlocks.map((block) => ({
            id: nextId("templateBlock"),
            templateId,
            startTime: block.startTime,
            endTime: block.endTime,
            title: block.title,
            memo: block.memo || null,
            sortOrder: block.sortOrder,
            createdAt: now,
            updatedAt: now
          }));
          return sendJson(res, 200, template);
        }
        return methodNotAllowed(res);
      }

      if (parts.length === 4 && parts[3] === "copy" && method === "POST") {
        const templateId = parseId(parts[2]);
        if (!templateId) return notFound(res);
        const source = store.templates.find((t) => t.id === templateId && t.userId === userId);
        if (!source) return sendJson(res, 404, { message: "template not found" });

        const now = new Date().toISOString();
        const newId = nextId("template");
        const copy = {
          ...source,
          id: newId,
          name: `${source.name} (Copy)`,
          isDefault: false,
          createdAt: now,
          updatedAt: now,
          blocks: source.blocks.map((block) => ({
            ...block,
            id: nextId("templateBlock"),
            templateId: newId,
            createdAt: now,
            updatedAt: now
          }))
        };
        store.templates.push(copy);
        return sendJson(res, 201, copy);
      }

      if (parts.length === 4 && parts[3] === "default" && method === "PUT") {
        const templateId = parseId(parts[2]);
        if (!templateId) return notFound(res);
        const target = store.templates.find((t) => t.id === templateId && t.userId === userId);
        if (!target) return sendJson(res, 404, { message: "template not found" });

        for (const template of store.templates) {
          if (template.userId === userId) template.isDefault = false;
        }
        target.isDefault = true;
        target.updatedAt = new Date().toISOString();
        return sendJson(res, 200, target);
      }

      return notFound(res);
    }

    if (parts[0] === "api" && parts[1] === "daily-plans") {
      const auth = requireAuth(req, res);
      if (!auth) return;
      const userId = auth.user.id;

      if (parts.length === 2) {
        if (method === "GET") {
          const date = url.searchParams.get("date");
          let plans = store.dailyPlans.filter((p) => p.userId === userId);
          if (date) plans = plans.filter((p) => p.planDate === date);
          return sendJson(res, 200, plans);
        }
        if (method === "POST") {
          const body = await readBody(req);
          const { planDate, templateId = null, goals = [], timeBlocks = [] } = body;
          ensurePlanDate(planDate);
          const validGoals = validateGoals(goals);
          const validTimeBlocks = validateTimeBlocks(timeBlocks);
          const now = new Date().toISOString();
          const dailyPlanId = nextId("dailyPlan");

          const plan = {
            id: dailyPlanId,
            userId,
            planDate,
            templateId,
            createdAt: now,
            updatedAt: now,
            goals: validGoals.map((goal) => ({
              id: nextId("dailyGoal"),
              dailyPlanId,
              content: goal.content,
              isCompleted: goal.isCompleted,
              sortOrder: goal.sortOrder,
              createdAt: now,
              updatedAt: now
            })),
            timeBlocks: validTimeBlocks.map((block) => ({
              id: nextId("dailyTimeBlock"),
              dailyPlanId,
              startTime: block.startTime,
              endTime: block.endTime,
              title: block.title,
              memo: block.memo || null,
              isCompleted: Boolean(block.isCompleted),
              sortOrder: block.sortOrder,
              createdAt: now,
              updatedAt: now
            }))
          };

          store.dailyPlans.push(plan);
          return sendJson(res, 201, plan);
        }
        return methodNotAllowed(res);
      }

      if (parts.length === 3) {
        const planId = parseId(parts[2]);
        if (!planId) return notFound(res);
        const plan = findPlanById(userId, planId);
        if (!plan) return sendJson(res, 404, { message: "daily plan not found" });

        if (method === "GET") return sendJson(res, 200, plan);
        if (method === "DELETE") {
          const idx = store.dailyPlans.findIndex((p) => p.id === planId && p.userId === userId);
          store.dailyPlans.splice(idx, 1);
          return sendNoContent(res);
        }
        if (method === "PUT") {
          const body = await readBody(req);
          const { planDate, templateId = null, goals = [], timeBlocks = [] } = body;
          ensurePlanDate(planDate);
          const validGoals = validateGoals(goals);
          const validTimeBlocks = validateTimeBlocks(timeBlocks);
          const now = new Date().toISOString();
          plan.planDate = planDate;
          plan.templateId = templateId;
          plan.updatedAt = now;
          plan.goals = validGoals.map((goal) => ({
            id: nextId("dailyGoal"),
            dailyPlanId: plan.id,
            content: goal.content,
            isCompleted: goal.isCompleted,
            sortOrder: goal.sortOrder,
            createdAt: now,
            updatedAt: now
          }));
          plan.timeBlocks = validTimeBlocks.map((block) => ({
            id: nextId("dailyTimeBlock"),
            dailyPlanId: plan.id,
            startTime: block.startTime,
            endTime: block.endTime,
            title: block.title,
            memo: block.memo || null,
            isCompleted: Boolean(block.isCompleted),
            sortOrder: block.sortOrder,
            createdAt: now,
            updatedAt: now
          }));
          return sendJson(res, 200, plan);
        }
        return methodNotAllowed(res);
      }

      if (parts.length === 4 && parts[2] === "from-template" && method === "POST") {
        const templateId = parseId(parts[3]);
        if (!templateId) return notFound(res);
        const template = store.templates.find((t) => t.id === templateId && t.userId === userId);
        if (!template) return sendJson(res, 404, { message: "template not found" });

        const body = await readBody(req);
        ensurePlanDate(body.planDate);
        const now = new Date().toISOString();
        const dailyPlanId = nextId("dailyPlan");
        const plan = {
          id: dailyPlanId,
          userId,
          planDate: body.planDate,
          templateId,
          createdAt: now,
          updatedAt: now,
          goals: [],
          timeBlocks: template.blocks.map((block) => ({
            id: nextId("dailyTimeBlock"),
            dailyPlanId,
            startTime: block.startTime,
            endTime: block.endTime,
            title: block.title,
            memo: block.memo || null,
            isCompleted: false,
            sortOrder: block.sortOrder,
            createdAt: now,
            updatedAt: now
          }))
        };
        store.dailyPlans.push(plan);
        return sendJson(res, 201, plan);
      }

      return notFound(res);
    }

    return notFound(res);
  } catch (error) {
    return sendJson(res, 400, { message: error.message });
  }
});

const port = process.env.PORT || 3000;
server.listen(port, () => {
  console.log(`TimeBox Planner backend listening on :${port}`);
});

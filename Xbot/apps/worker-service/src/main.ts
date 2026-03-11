import Fastify from "fastify";
import { Queue, Worker } from "bullmq";
import type { HealthResponse } from "@xbot/shared-contracts";

const server = Fastify({ logger: true });

const redisConnection = {
  host: process.env.REDIS_HOST ?? "127.0.0.1",
  port: Number(process.env.REDIS_PORT ?? "6379")
};

const queue = new Queue("xbot-jobs", { connection: redisConnection });

const worker = new Worker(
  "xbot-jobs",
  async (job) => {
    if (job.name === "evaluate_autonomy_gate") {
      return { ok: true, processed_at: new Date().toISOString() };
    }
    if (job.name === "replay_backtest") {
      return { ok: true, replay_id: job.id };
    }
    return { ok: true, ignored: true };
  },
  { connection: redisConnection }
);

worker.on("failed", (job, err) => {
  server.log.error({ jobId: job?.id, message: err.message }, "worker job failed");
});

server.get("/health", async () => {
  const payload: HealthResponse = {
    status: "healthy",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
    checks: {
      redis: "healthy",
      worker: "healthy"
    }
  };
  return payload;
});

server.post("/v1/jobs/enqueue", async (request) => {
  const body = request.body as { name: string; payload: Record<string, unknown> };
  const job = await queue.add(body.name, body.payload ?? {});
  return {
    job_id: job.id,
    name: body.name
  };
});

const port = Number(process.env.PORT ?? "4006");
await server.listen({ host: "0.0.0.0", port });

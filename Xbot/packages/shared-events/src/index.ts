import { randomUUID } from "node:crypto";
import { appendFile } from "node:fs/promises";
import type { EventEnvelope } from "@xbot/shared-contracts";

export type EventHandler = (event: EventEnvelope) => Promise<void> | void;

export interface EventBus {
  publish(event: EventEnvelope): Promise<void>;
  subscribe(eventType: string, handler: EventHandler): void;
}

export class InMemoryEventBus implements EventBus {
  private handlers = new Map<string, EventHandler[]>();

  async publish(event: EventEnvelope): Promise<void> {
    const list = this.handlers.get(event.event_type) ?? [];
    for (const handler of list) {
      await handler(event);
    }
  }

  subscribe(eventType: string, handler: EventHandler): void {
    const list = this.handlers.get(eventType) ?? [];
    list.push(handler);
    this.handlers.set(eventType, list);
  }
}

export function createEventEnvelope(
  service: string,
  eventType: string,
  correlationId: string,
  policyVersion: string,
  payload: Record<string, unknown>
): EventEnvelope {
  return {
    event_id: randomUUID(),
    event_type: eventType,
    correlation_id: correlationId,
    timestamp: new Date().toISOString(),
    service,
    policy_version: policyVersion,
    payload
  };
}

export class JsonlLedger {
  constructor(private readonly path: string) {}

  async append(event: EventEnvelope): Promise<void> {
    const line = JSON.stringify(event);
    await appendFile(this.path, `${line}\n`, { encoding: "utf8" });
  }
}

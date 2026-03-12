import { randomUUID } from "node:crypto";
import type { OrderRequest } from "@xbot/shared-contracts";
import type { ExecutionResult, VenueAdapter } from "./adapter.js";

export class PolymarketAdapter implements VenueAdapter {
  readonly name = "polymarket";
  private readonly baseUrl: string;
  private readonly orderEndpoint: string;
  private readonly cancelEndpoint: string;
  private readonly executionMode: "paper" | "live";
  private readonly allowLive: boolean;
  private readonly apiKey?: string;
  private readonly privateKey?: string;

  constructor(baseUrl = process.env.POLYMARKET_API_BASE ?? "https://clob.polymarket.com") {
    this.baseUrl = baseUrl;
    this.orderEndpoint = process.env.POLYMARKET_ORDER_ENDPOINT ?? "/order";
    this.cancelEndpoint = process.env.POLYMARKET_CANCEL_ENDPOINT ?? "/order/cancel";
    this.executionMode = process.env.EXECUTION_MODE === "live" ? "live" : "paper";
    this.allowLive = process.env.POLYMARKET_ALLOW_LIVE === "true";
    this.apiKey = process.env.POLYMARKET_API_KEY;
    this.privateKey = process.env.POLYMARKET_PRIVATE_KEY;
  }

  async createOrder(order: OrderRequest): Promise<ExecutionResult> {
    if (this.executionMode !== "live" || !this.allowLive) {
      return {
        venue_order_id: `poly_${randomUUID()}`,
        status: "submitted",
        submitted_at: new Date().toISOString(),
        raw: {
          simulated: true,
          mode: this.executionMode,
          allow_live: this.allowLive,
          baseUrl: this.baseUrl,
          market_id: order.market_id
        }
      };
    }

    if (!this.privateKey) {
      throw new Error(
        "POLYMARKET_PRIVATE_KEY is required when EXECUTION_MODE=live and POLYMARKET_ALLOW_LIVE=true"
      );
    }

    const payload = {
      market: order.market_id,
      side: order.side,
      size: order.quantity,
      price: order.limit_price,
      client_order_id: order.request_id
    };

    const response = await fetch(`${this.baseUrl}${this.orderEndpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.apiKey ? { Authorization: `Bearer ${this.apiKey}` } : {}),
        "X-Private-Key-Present": "true"
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10_000)
    });

    const responseText = await response.text();
    if (!response.ok) {
      throw new Error(
        `polymarket_order_failed status=${response.status} body=${responseText.slice(0, 300)}`
      );
    }

    let parsed: Record<string, unknown> = {};
    try {
      parsed = JSON.parse(responseText) as Record<string, unknown>;
    } catch {
      parsed = { raw: responseText };
    }

    const venueOrderId =
      (parsed.order_id as string | undefined) ??
      (parsed.id as string | undefined) ??
      `poly_${randomUUID()}`;

    return {
      venue_order_id: venueOrderId,
      status: "submitted",
      submitted_at: new Date().toISOString(),
      raw: parsed
    };
  }

  async cancelOrder(orderId: string): Promise<{ cancelled: boolean; venue_order_id: string }> {
    if (this.executionMode !== "live" || !this.allowLive) {
      return {
        cancelled: true,
        venue_order_id: orderId
      };
    }

    const response = await fetch(`${this.baseUrl}${this.cancelEndpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.apiKey ? { Authorization: `Bearer ${this.apiKey}` } : {})
      },
      body: JSON.stringify({ order_id: orderId }),
      signal: AbortSignal.timeout(10_000)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(
        `polymarket_cancel_failed status=${response.status} body=${text.slice(0, 300)}`
      );
    }

    return {
      cancelled: true,
      venue_order_id: orderId
    };
  }
}

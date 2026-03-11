import { randomUUID } from "node:crypto";
import type { OrderRequest } from "@xbot/shared-contracts";
import type { ExecutionResult, VenueAdapter } from "./adapter.js";

export class PolymarketAdapter implements VenueAdapter {
  readonly name = "polymarket";
  private readonly baseUrl: string;

  constructor(baseUrl = process.env.POLYMARKET_API_BASE ?? "https://clob.polymarket.com") {
    this.baseUrl = baseUrl;
  }

  async createOrder(order: OrderRequest): Promise<ExecutionResult> {
    return {
      venue_order_id: `poly_${randomUUID()}`,
      status: "submitted",
      submitted_at: new Date().toISOString(),
      raw: {
        simulated: true,
        baseUrl: this.baseUrl,
        market_id: order.market_id
      }
    };
  }

  async cancelOrder(orderId: string): Promise<{ cancelled: boolean; venue_order_id: string }> {
    return {
      cancelled: true,
      venue_order_id: orderId
    };
  }
}

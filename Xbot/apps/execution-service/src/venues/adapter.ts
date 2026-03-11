import type { OrderRequest, OrderStatus } from "@xbot/shared-contracts";

export interface ExecutionResult {
  venue_order_id: string;
  status: OrderStatus;
  submitted_at: string;
  raw?: Record<string, unknown>;
}

export interface VenueAdapter {
  readonly name: string;
  createOrder(order: OrderRequest): Promise<ExecutionResult>;
  cancelOrder(orderId: string): Promise<{ cancelled: boolean; venue_order_id: string }>;
}

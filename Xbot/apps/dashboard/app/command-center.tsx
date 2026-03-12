"use client";

import { FormEvent, startTransition, useEffect, useState } from "react";

type JsonValue = Record<string, unknown> | null;

const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:4001";

async function fetchJson(path: string): Promise<JsonValue> {
  try {
    const response = await fetch(`${gatewayUrl}${path}`);
    if (!response.ok) return null;
    return (await response.json()) as JsonValue;
  } catch {
    return null;
  }
}

async function postJson(path: string, body: Record<string, unknown>): Promise<JsonValue> {
  try {
    const response = await fetch(`${gatewayUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    return (await response.json()) as JsonValue;
  } catch {
    return null;
  }
}

async function putJson(path: string, body: Record<string, unknown>): Promise<JsonValue> {
  try {
    const response = await fetch(`${gatewayUrl}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    return (await response.json()) as JsonValue;
  } catch {
    return null;
  }
}

type DashboardState = {
  health: JsonValue;
  mode: JsonValue;
  gate: JsonValue;
  overview: JsonValue;
  approvals: JsonValue;
  positions: JsonValue;
};

const emptyState: DashboardState = {
  health: null,
  mode: null,
  gate: null,
  overview: null,
  approvals: null,
  positions: null
};

export function CommandCenter() {
  const [state, setState] = useState<DashboardState>(emptyState);
  const [lastAction, setLastAction] = useState<string>("idle");
  const [marketId, setMarketId] = useState<string>("poly-pres-2028-win");
  const [killReason, setKillReason] = useState<string>("manual_kill_switch");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  const pendingApprovals =
    (state.approvals?.items as Array<Record<string, unknown>> | undefined) ?? [];

  async function refresh() {
    const [health, mode, gate, overview, approvals, positions] = await Promise.all([
      fetchJson("/health"),
      fetchJson("/v1/autonomy/mode"),
      fetchJson("/v1/autonomy/gate"),
      fetchJson("/v1/analytics/overview"),
      fetchJson("/v1/approvals/pending"),
      fetchJson("/v1/positions")
    ]);
    setState({ health, mode, gate, overview, approvals, positions });
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);

  function runAction(name: string, action: () => Promise<void>) {
    setIsBusy(true);
    setLastAction(name);
    startTransition(() => {
      action()
        .catch(() => {
          setLastAction(`${name}:failed`);
        })
        .finally(() => {
          setIsBusy(false);
          refresh();
        });
    });
  }

  function onSignalSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    runAction("generate_signal", async () => {
      await postJson("/v1/signals/generate", { market_id: marketId });
    });
  }

  return (
    <main className="container">
      <h1>Xbot Trading Command Center</h1>
      <p className="muted">Internal-only dashboard for live-safe autonomous trading operations.</p>

      <section className="grid cards" style={{ marginTop: 18 }}>
        <article className="card">
          <span className="pill">Autonomy Mode</span>
          <h2>{String(state.mode?.mode ?? "unknown")}</h2>
          <p className="muted">Last action: {lastAction}</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {["approval_required", "paper_autonomous", "live_autonomous"].map((mode) => (
              <button
                key={mode}
                className="btn"
                onClick={() =>
                  runAction(`mode:${mode}`, async () => {
                    await putJson("/v1/autonomy/mode", { mode });
                  })
                }
                disabled={isBusy}
              >
                {mode}
              </button>
            ))}
          </div>
        </article>

        <article className="card">
          <span className="pill">Autonomy Gate</span>
          <h2
            className={(state.gate?.passed as boolean | undefined) ? "success" : "danger"}
          >
            {(state.gate?.passed as boolean | undefined) ? "PASS" : "BLOCKED"}
          </h2>
          <p className="muted">
            {((state.gate?.failures as string[] | undefined) ?? []).join(", ") ||
              "All checks passing"}
          </p>
        </article>

        <article className="card">
          <span className="pill">Pending Approvals</span>
          <h2>{String(state.approvals?.count ?? 0)}</h2>
          <p className="muted">Orders waiting for operator confirmation.</p>
        </article>

        <article className="card">
          <span className="pill">Open Positions</span>
          <h2>{String(state.overview?.active_positions ?? 0)}</h2>
          <p className="muted">Total exposure: {String(state.overview?.exposure ?? 0)}</p>
        </article>
      </section>

      <section className="card" style={{ marginTop: 16 }}>
        <div className="row">
          <h3>Signal Generator</h3>
          <span className="pill">Hybrid strategy</span>
        </div>
        <form className="row" onSubmit={onSignalSubmit}>
          <input
            className="input"
            value={marketId}
            onChange={(event) => setMarketId(event.target.value)}
            placeholder="market id"
          />
          <button className="btn primary" type="submit" disabled={isBusy}>
            Generate Signal
          </button>
        </form>
      </section>

      <section className="card" style={{ marginTop: 16 }}>
        <div className="row">
          <h3>Kill Switch</h3>
          <span className="danger">Emergency stop</span>
        </div>
        <div className="row">
          <input
            className="input"
            value={killReason}
            onChange={(event) => setKillReason(event.target.value)}
            placeholder="reason"
          />
          <button
            className="btn danger-btn"
            disabled={isBusy}
            onClick={() =>
              runAction("kill_switch", async () => {
                await postJson("/v1/autonomy/kill-switch", { reason: killReason });
              })
            }
          >
            Activate Kill Switch
          </button>
          <button
            className="btn"
            disabled={isBusy}
            onClick={() =>
              runAction("resume", async () => {
                await postJson("/v1/autonomy/resume", { mode: "approval_required" });
              })
            }
          >
            Resume (Approval Required)
          </button>
        </div>
      </section>

      <section className="card" style={{ marginTop: 16 }}>
        <h3>Pending Approval Queue</h3>
        {pendingApprovals.length === 0 ? (
          <p className="muted">No pending approvals.</p>
        ) : (
          <div className="grid" style={{ gap: 8 }}>
            {pendingApprovals.map((item) => {
              const request = (item.request as Record<string, unknown> | undefined) ?? {};
              const requestId = String(request.request_id ?? "");
              return (
                <div className="card-lite" key={requestId}>
                  <div className="row">
                    <strong>{requestId}</strong>
                    <span className="pill">{String(request.market_id ?? "unknown_market")}</span>
                  </div>
                  <div className="row">
                    <span>
                      {String(request.side ?? "buy")} {String(request.quantity ?? 0)} @{" "}
                      {String(request.limit_price ?? 0)}
                    </span>
                    <span className="muted">
                      confidence {String(request.confidence ?? "0")}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      className="btn primary"
                      disabled={isBusy}
                      onClick={() =>
                        runAction(`approve:${requestId}`, async () => {
                          await postJson("/v1/approvals/decision", {
                            approval_id: `approval_${requestId}`,
                            request_id: requestId,
                            approved: true,
                            actor_id: "operator_dashboard"
                          });
                        })
                      }
                    >
                      Approve
                    </button>
                    <button
                      className="btn danger-btn"
                      disabled={isBusy}
                      onClick={() =>
                        runAction(`reject:${requestId}`, async () => {
                          await postJson("/v1/approvals/decision", {
                            approval_id: `rejection_${requestId}`,
                            request_id: requestId,
                            approved: false,
                            actor_id: "operator_dashboard",
                            reason: "manual_reject"
                          });
                        })
                      }
                    >
                      Reject
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="card" style={{ marginTop: 16 }}>
        <div className="row">
          <h3>System Health</h3>
          <span
            className={`pill ${
              state.health?.status === "healthy" ? "success" : "danger"
            }`}
          >
            {String(state.health?.status ?? "unknown")}
          </span>
        </div>
        <pre>{JSON.stringify(state.health?.checks ?? {}, null, 2)}</pre>
      </section>
    </main>
  );
}

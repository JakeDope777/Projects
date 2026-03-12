"use client";

import { FormEvent, startTransition, useEffect, useState } from "react";

type JsonValue = Record<string, unknown> | null;

const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:4001";
const TOKEN_KEY = "xbot_access_token";
const REFRESH_KEY = "xbot_refresh_token";

type DashboardState = {
  health: JsonValue;
  mode: JsonValue;
  gate: JsonValue;
  overview: JsonValue;
  approvals: JsonValue;
  positions: JsonValue;
};

type UserSession = {
  user: { id: string; email: string; role: string } | null;
  accessToken: string | null;
  refreshToken: string | null;
  authRequired: boolean;
};

const emptyState: DashboardState = {
  health: null,
  mode: null,
  gate: null,
  overview: null,
  approvals: null,
  positions: null
};

const emptySession: UserSession = {
  user: null,
  accessToken: null,
  refreshToken: null,
  authRequired: true
};

export function CommandCenter() {
  const [state, setState] = useState<DashboardState>(emptyState);
  const [session, setSession] = useState<UserSession>(emptySession);
  const [lastAction, setLastAction] = useState<string>("idle");
  const [marketId, setMarketId] = useState<string>("poly-pres-2028-win");
  const [killReason, setKillReason] = useState<string>("manual_kill_switch");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [loginEmail, setLoginEmail] = useState<string>("operator@xbot.local");
  const [loginPassword, setLoginPassword] = useState<string>("ChangeMe!123");
  const [loginError, setLoginError] = useState<string>("");

  const pendingApprovals =
    (state.approvals?.items as Array<Record<string, unknown>> | undefined) ?? [];

  function saveSessionTokens(accessToken: string | null, refreshToken: string | null) {
    if (typeof window === "undefined") return;
    if (accessToken) {
      window.localStorage.setItem(TOKEN_KEY, accessToken);
    } else {
      window.localStorage.removeItem(TOKEN_KEY);
    }
    if (refreshToken) {
      window.localStorage.setItem(REFRESH_KEY, refreshToken);
    } else {
      window.localStorage.removeItem(REFRESH_KEY);
    }
  }

  async function refreshAccessToken(currentRefreshToken: string) {
    const response = await fetch(`${gatewayUrl}/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: currentRefreshToken })
    });
    if (!response.ok) return null;
    const payload = (await response.json()) as { access_token?: string };
    return payload.access_token ?? null;
  }

  async function requestJson(
    path: string,
    method: "GET" | "POST" | "PUT" = "GET",
    body?: Record<string, unknown>
  ): Promise<{ status: number; payload: JsonValue }> {
    let currentAccessToken = session.accessToken;
    let currentRefreshToken = session.refreshToken;
    const headers: Record<string, string> = {
      "Content-Type": "application/json"
    };
    if (currentAccessToken) {
      headers.Authorization = `Bearer ${currentAccessToken}`;
    }

    const firstResponse = await fetch(`${gatewayUrl}${path}`, {
      method,
      headers,
      ...(body ? { body: JSON.stringify(body) } : {})
    });

    if (
      firstResponse.status === 401 &&
      currentRefreshToken &&
      session.authRequired
    ) {
      const newAccessToken = await refreshAccessToken(currentRefreshToken);
      if (newAccessToken) {
        currentAccessToken = newAccessToken;
        saveSessionTokens(newAccessToken, currentRefreshToken);
        setSession((prev) => ({ ...prev, accessToken: newAccessToken }));
        const retryHeaders: Record<string, string> = {
          "Content-Type": "application/json",
          Authorization: `Bearer ${newAccessToken}`
        };
        const retryResponse = await fetch(`${gatewayUrl}${path}`, {
          method,
          headers: retryHeaders,
          ...(body ? { body: JSON.stringify(body) } : {})
        });
        const retryPayload = (await retryResponse.json()) as JsonValue;
        return { status: retryResponse.status, payload: retryPayload };
      }
    }

    const payload = (await firstResponse.json()) as JsonValue;
    return { status: firstResponse.status, payload };
  }

  async function syncAuthState() {
    if (typeof window === "undefined") return;
    const storedAccess = window.localStorage.getItem(TOKEN_KEY);
    const storedRefresh = window.localStorage.getItem(REFRESH_KEY);
    setSession((prev) => ({
      ...prev,
      accessToken: storedAccess,
      refreshToken: storedRefresh
    }));

    const headers: Record<string, string> = {};
    if (storedAccess) {
      headers.Authorization = `Bearer ${storedAccess}`;
    }
    const response = await fetch(`${gatewayUrl}/v1/auth/me`, { headers });
    if (response.ok) {
      const payload = (await response.json()) as {
        user?: { id: string; email: string; role: string };
        auth_required?: boolean;
      };
      setSession((prev) => ({
        ...prev,
        user: payload.user ?? null,
        authRequired: payload.auth_required ?? true
      }));
      return;
    }
    setSession((prev) => ({
      ...prev,
      user: null
    }));
  }

  async function refreshDashboardData() {
    const [health, mode, gate, overview, approvals, positions] = await Promise.all([
      requestJson("/health"),
      requestJson("/v1/autonomy/mode"),
      requestJson("/v1/autonomy/gate"),
      requestJson("/v1/analytics/overview"),
      requestJson("/v1/approvals/pending"),
      requestJson("/v1/positions")
    ]);
    setState({
      health: health.payload,
      mode: mode.payload,
      gate: gate.payload,
      overview: overview.payload,
      approvals: approvals.payload,
      positions: positions.payload
    });
  }

  useEffect(() => {
    syncAuthState().then(() => {
      refreshDashboardData();
    });
    const interval = setInterval(refreshDashboardData, 5000);
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
          refreshDashboardData();
        });
    });
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginError("");
    setIsBusy(true);
    const response = await fetch(`${gatewayUrl}/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: loginEmail,
        password: loginPassword
      })
    });
    if (!response.ok) {
      setIsBusy(false);
      setLoginError("Invalid credentials");
      return;
    }
    const payload = (await response.json()) as {
      user: { id: string; email: string; role: string };
      access_token: string;
      refresh_token: string;
    };
    saveSessionTokens(payload.access_token, payload.refresh_token);
    setSession({
      user: payload.user,
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      authRequired: true
    });
    setIsBusy(false);
    refreshDashboardData();
  }

  function handleLogout() {
    saveSessionTokens(null, null);
    setSession({
      user: null,
      accessToken: null,
      refreshToken: null,
      authRequired: true
    });
  }

  function onSignalSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    runAction("generate_signal", async () => {
      await requestJson("/v1/signals/generate", "POST", { market_id: marketId });
    });
  }

  if (session.authRequired && !session.user) {
    return (
      <main className="container">
        <h1>Xbot Operator Login</h1>
        <p className="muted">Authenticate to access trading controls.</p>
        <section className="card" style={{ marginTop: 16, maxWidth: 520 }}>
          <form className="grid" style={{ gap: 12 }} onSubmit={handleLogin}>
            <input
              className="input"
              value={loginEmail}
              onChange={(event) => setLoginEmail(event.target.value)}
              placeholder="email"
              type="email"
            />
            <input
              className="input"
              value={loginPassword}
              onChange={(event) => setLoginPassword(event.target.value)}
              placeholder="password"
              type="password"
            />
            <button className="btn primary" type="submit" disabled={isBusy}>
              Sign In
            </button>
            {loginError ? <p className="danger">{loginError}</p> : null}
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="container">
      <h1>Xbot Trading Command Center</h1>
      <p className="muted">Internal-only dashboard for live-safe autonomous trading operations.</p>

      <section className="card" style={{ marginTop: 12 }}>
        <div className="row">
          <span className="pill">
            {session.user?.email ?? "operator"} ({session.user?.role ?? "n/a"})
          </span>
          {session.authRequired ? (
            <button className="btn" onClick={handleLogout}>
              Logout
            </button>
          ) : (
            <span className="muted">Auth disabled</span>
          )}
        </div>
      </section>

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
                    await requestJson("/v1/autonomy/mode", "PUT", { mode });
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
                await requestJson("/v1/autonomy/kill-switch", "POST", {
                  reason: killReason
                });
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
                await requestJson("/v1/autonomy/resume", "POST", {
                  mode: "approval_required"
                });
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
                          await requestJson("/v1/approvals/decision", "POST", {
                            approval_id: `approval_${requestId}`,
                            request_id: requestId,
                            approved: true,
                            actor_id: session.user?.id ?? "operator_dashboard"
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
                          await requestJson("/v1/approvals/decision", "POST", {
                            approval_id: `rejection_${requestId}`,
                            request_id: requestId,
                            approved: false,
                            actor_id: session.user?.id ?? "operator_dashboard",
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


const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:4001";

async function getJson(path: string) {
  try {
    const res = await fetch(`${gatewayUrl}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const [health, mode, gate, overview, approvals] = await Promise.all([
    getJson("/health"),
    getJson("/v1/autonomy/mode"),
    getJson("/v1/autonomy/gate"),
    getJson("/v1/analytics/overview"),
    getJson("/v1/approvals/pending")
  ]);

  return (
    <main className="container">
      <h1>Xbot Trading Command Center</h1>
      <p className="muted">Internal-only dashboard for live-safe autonomous trading operations.</p>

      <section className="grid cards" style={{ marginTop: 18 }}>
        <article className="card">
          <span className="pill">Autonomy Mode</span>
          <h2>{mode?.mode ?? "unknown"}</h2>
          <p className="muted">Default launch mode is approval-required.</p>
        </article>
        <article className="card">
          <span className="pill">Autonomy Gate</span>
          <h2 className={gate?.passed ? "success" : "danger"}>{gate?.passed ? "PASS" : "BLOCKED"}</h2>
          <p className="muted">{(gate?.failures ?? []).join(", ") || "All checks passing"}</p>
        </article>
        <article className="card">
          <span className="pill">Pending Approvals</span>
          <h2>{approvals?.count ?? 0}</h2>
          <p className="muted">Orders waiting for operator confirmation.</p>
        </article>
        <article className="card">
          <span className="pill">Open Positions</span>
          <h2>{overview?.active_positions ?? 0}</h2>
          <p className="muted">Total exposure: {overview?.exposure ?? 0}</p>
        </article>
      </section>

      <section className="card" style={{ marginTop: 16 }}>
        <div className="row">
          <h3>System Health</h3>
          <span className={`pill ${health?.status === "healthy" ? "success" : "danger"}`}>{health?.status ?? "unknown"}</span>
        </div>
        <pre>{JSON.stringify(health?.checks ?? {}, null, 2)}</pre>
      </section>

      <section className="card" style={{ marginTop: 16 }}>
        <h3>Risk KPI Snapshot</h3>
        <div className="row">
          <span>Critical breaches</span>
          <strong>{overview?.kpi?.critical_breaches ?? 0}</strong>
        </div>
        <div className="row">
          <span>Risk-adjusted target</span>
          <strong>{overview?.kpi?.risk_adjusted_return_target ?? "n/a"}</strong>
        </div>
      </section>
    </main>
  );
}


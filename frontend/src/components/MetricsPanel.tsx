import type { MetricsSnapshot } from "../types";

interface MetricsPanelProps {
  metrics?: MetricsSnapshot;
}

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  const decision = metrics?.decision_latency_ms ?? {};
  const rtt = metrics?.round_trip_latency_ms ?? {};
  return (
    <div>
      <div className="panel-header">
        <h2>Metrics</h2>
        <span>{metrics?.total_trades ?? 0} trades</span>
      </div>
      <div className="metric-grid">
        <div className="metric-card"><span>Decision p50</span><strong>{decision.p50 ?? 0} ms</strong></div>
        <div className="metric-card"><span>Decision p95</span><strong>{decision.p95 ?? 0} ms</strong></div>
        <div className="metric-card"><span>Decision p99</span><strong>{decision.p99 ?? 0} ms</strong></div>
        <div className="metric-card"><span>RTT p95</span><strong>{rtt.p95 ?? 0} ms</strong></div>
        <div className="metric-card"><span>Events/sec</span><strong>{metrics?.events_per_sec ?? 0}</strong></div>
        <div className="metric-card"><span>Fills/sec</span><strong>{metrics?.fills_per_sec ?? 0}</strong></div>
      </div>
    </div>
  );
}

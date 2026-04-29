import type { RiskState } from "../types";

interface RiskPanelProps {
  risk?: RiskState;
  onToggleKillSwitch: (enabled: boolean) => Promise<void>;
}

export default function RiskPanel({ risk, onToggleKillSwitch }: RiskPanelProps) {
  return (
    <div>
      <div className="panel-header">
        <h2>Risk</h2>
        <button className={risk?.kill_switch_enabled ? "warn" : "muted"} onClick={() => onToggleKillSwitch(!risk?.kill_switch_enabled)}>
          {risk?.kill_switch_enabled ? "Disable Kill" : "Trigger Kill"}
        </button>
      </div>
      <div className="keyvals">
        <div><span>Max order qty</span><strong>{risk?.max_order_qty ?? 0}</strong></div>
        <div><span>Max position</span><strong>{risk?.max_position_per_symbol ?? 0}</strong></div>
        <div><span>Daily loss</span><strong>{risk?.max_daily_loss ?? 0}</strong></div>
        <div><span>Price band</span><strong>{risk?.max_price_deviation_bps ?? 0} bps</strong></div>
      </div>
      <h3>Recent Breaches</h3>
      <div className="stack tight">
        {(risk?.last_rejections ?? []).slice(0, 5).map((entry, index) => (
          <div className="log-row" key={index}>
            <span>{String(entry.symbol)}</span>
            <strong>{String(entry.reason)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

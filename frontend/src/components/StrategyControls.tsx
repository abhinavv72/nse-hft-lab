import type { StrategyState } from "../types";

interface StrategyControlsProps {
  strategies: Record<string, StrategyState>;
  selectedSymbol: string;
  session: {
    strategyDrafts: Record<string, Partial<StrategyState["config"]>>;
    updateDraft: (strategyId: string, patch: Partial<StrategyState["config"]>) => void;
    startStrategy: (strategyId: string, payload: Record<string, unknown>) => Promise<void>;
    stopStrategy: (strategyId: string) => Promise<void>;
  };
}

export default function StrategyControls({ strategies, selectedSymbol, session }: StrategyControlsProps) {
  return (
    <div>
      <div className="panel-header">
        <h2>Strategy Control</h2>
        <span>{selectedSymbol}</span>
      </div>
      <div className="stack">
        {Object.values(strategies).map((strategy) => {
          const draft = session.strategyDrafts[strategy.strategy_id] ?? {};
          return (
            <div className="strategy-card" key={strategy.strategy_id}>
              <div className="strategy-topline">
                <strong>{strategy.kind}</strong>
                <span className={strategy.enabled ? "pill ok" : "pill"}>{strategy.enabled ? "running" : "stopped"}</span>
              </div>
              <div className="form-grid">
                <label>
                  Symbol
                  <input
                    value={(draft.symbol as string) ?? strategy.symbol}
                    onChange={(event) => session.updateDraft(strategy.strategy_id, { symbol: event.target.value })}
                  />
                </label>
                <label>
                  Qty
                  <input
                    type="number"
                    value={(draft.qty as number) ?? strategy.config.qty}
                    onChange={(event) => session.updateDraft(strategy.strategy_id, { qty: Number(event.target.value) })}
                  />
                </label>
                <label>
                  Spread bps
                  <input
                    type="number"
                    value={(draft.spread_bps as number) ?? strategy.config.spread_bps}
                    onChange={(event) => session.updateDraft(strategy.strategy_id, { spread_bps: Number(event.target.value) })}
                  />
                </label>
                <label>
                  Threshold
                  <input
                    type="number"
                    value={(draft.threshold_bps as number) ?? strategy.config.threshold_bps}
                    onChange={(event) => session.updateDraft(strategy.strategy_id, { threshold_bps: Number(event.target.value) })}
                  />
                </label>
              </div>
              <div className="row-actions">
                <button onClick={() => session.startStrategy(strategy.strategy_id, draft)}>Start</button>
                <button className="muted" onClick={() => session.stopStrategy(strategy.strategy_id)}>Stop</button>
                <span className="subtle">{strategy.last_action ?? "idle"}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

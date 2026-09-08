import type { DashboardState } from "../types";

interface HeaderProps {
  connected: boolean;
  state: DashboardState | null;
  activeView: string;
  onChangeView: (view: "watchlist" | "ipo" | "simulator" | "learn") => void;
  onLogout: () => void;
}

export default function Header({ connected, state, activeView, onChangeView, onLogout }: HeaderProps) {

  return (
    <header className="header glass-header">
      <div className="header-brand">
        <p className="eyebrow">INDIAN MARKET RESEARCH LAB</p>
        <h1>TradeStock Pulse</h1>
        <div className="status-bar">
          <span className={`status-indicator ${connected ? "online" : "offline"}`}></span>
          <p className="subtle">
            {connected ? "Live data connected" : "Connecting to market data"} • Simulator {state?.session.market_running ? "running" : "paused"}
          </p>
        </div>
        <p className="simulation-notice">Educational simulation only — not investment advice or broker execution.</p>
      </div>
      <div className="header-controls product-nav" aria-label="Main navigation">
        {(["watchlist", "ipo", "simulator", "learn"] as const).map((view) => (
          <button key={view} className={activeView === view ? "active-nav" : "muted"} onClick={() => onChangeView(view)}>
            {view === "ipo" ? "IPO Research" : view[0].toUpperCase() + view.slice(1)}
          </button>
        ))}
        <button className="muted" onClick={onLogout}>Exit</button>
      </div>
    </header>
  );
}

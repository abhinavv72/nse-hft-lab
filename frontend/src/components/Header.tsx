import type { DashboardState } from "../types";

interface HeaderProps {
  connected: boolean;
  state: DashboardState | null;
  session: {
    replaySessions: string[];
    startMarket: (speed: number) => Promise<void>;
    stopMarket: () => Promise<void>;
    resetMarket: () => Promise<void>;
    injectVolatility: () => Promise<void>;
    exportSession: () => Promise<void>;
    startReplay: (sessionId: string, speed: number) => Promise<void>;
  };
}

export default function Header({ connected, state, session }: HeaderProps) {
  const latestReplay = session.replaySessions[0];

  return (
    <header className="header">
      <div>
        <p className="eyebrow">LOCAL-FIRST HFT LAB</p>
        <h1>NSE-HFT-Lab</h1>
        <p className="subtle">
          Session {state?.session.session_id ?? "booting"} • {state?.session.mode ?? "live"} • {connected ? "ws connected" : "ws offline"}
        </p>
      </div>
      <div className="header-controls">
        <button onClick={() => session.startMarket(1)}>Start 1x</button>
        <button onClick={() => session.startMarket(5)}>Start 5x</button>
        <button onClick={() => session.startMarket(20)}>Start 20x</button>
        <button className="muted" onClick={() => session.stopMarket()}>Stop</button>
        <button className="muted" onClick={() => session.resetMarket()}>Reset</button>
        <button className="warn" onClick={() => session.injectVolatility()}>Vol Spike</button>
        <button className="muted" onClick={() => session.exportSession()}>Export</button>
        <button disabled={!latestReplay} onClick={() => latestReplay && session.startReplay(latestReplay, 5)}>Replay Latest</button>
      </div>
    </header>
  );
}

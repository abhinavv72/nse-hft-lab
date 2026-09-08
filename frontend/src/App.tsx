import { useState } from "react";

import Header from "./components/Header";
import MarketWatch from "./components/MarketWatch";
import OrderBook from "./components/OrderBook";
import StrategyControls from "./components/StrategyControls";
import Blotter from "./components/Blotter";
import RiskPanel from "./components/RiskPanel";
import PortfolioPanel from "./components/PortfolioPanel";
import MetricsPanel from "./components/MetricsPanel";
import LogsPanel from "./components/LogsPanel";
import TopIdeasPanel from "./components/TopIdeasPanel";
import NewsFeedPanel from "./components/NewsFeedPanel";
import LoginPage from "./components/LoginPage";
import Watchlist from "./components/Watchlist";
import IpoResearch from "./components/IpoResearch";
import LearnPanel from "./components/LearnPanel";
import { useMarketStream } from "./hooks/useMarketStream";
import { useSessionState } from "./hooks/useSessionState";

export default function App() {
  const { state, connected } = useMarketStream();
  const session = useSessionState(state);
  const selectedSymbol = session.selectedSymbol;
  const [entered, setEntered] = useState(() => window.sessionStorage.getItem("tradepulse.entered") === "1");
  const [activeView, setActiveView] = useState<"watchlist" | "ipo" | "simulator" | "learn">("watchlist");

  const handleEnter = () => {
    window.sessionStorage.setItem("tradepulse.entered", "1");
    setEntered(true);
  };

  const handleLogout = () => {
    window.sessionStorage.removeItem("tradepulse.entered");
    setEntered(false);
  };

  const openSimulator = async (symbol?: string) => {
    if (symbol) await session.setSelectedSymbol(symbol);
    setActiveView("simulator");
  };

  return (
    <div className="app-shell">
      {!entered ? (
        <LoginPage onEnter={handleEnter} />
      ) : (
        <>
          <Header connected={connected} state={state} activeView={activeView} onChangeView={setActiveView} onLogout={handleLogout} />
          {!connected && (
            <section className="connection-banner" role="status">
              <strong>Backend not connected.</strong>
              <span>Waiting for the market service. Please refresh in a few seconds.</span>
            </section>
          )}
          {activeView === "watchlist" && <Watchlist ideas={state?.signals ?? []} market={state?.market ?? {}} onSimulate={openSimulator} onRefresh={session.refreshNews} />}
          {activeView === "ipo" && <IpoResearch articles={state?.news ?? []} />}
          {activeView === "learn" && <LearnPanel onOpenSimulator={() => openSimulator()} />}
          {activeView === "simulator" && <>
          <section className="simulator-intro">
            <div><p className="eyebrow">PAPER-TRADING WORKSPACE</p><h2>Test a strategy without real money.</h2><p>Start the replay, select a stock, then observe simulated orders, fills, P&amp;L, and risk controls.</p></div>
            <div className="simulator-actions"><button onClick={() => session.startMarket(1)}>Start replay</button><button className="muted" onClick={() => session.stopMarket()}>Pause</button><button className="muted" onClick={() => session.resetMarket()}>Reset</button><button className="warn" onClick={() => session.injectVolatility()}>Test volatility</button></div>
          </section>
          <main className="dashboard-grid simulator-grid">
            <section className="panel span-4">
              <MarketWatch
                market={state?.market ?? {}}
                selectedSymbol={selectedSymbol}
                onSelectSymbol={session.setSelectedSymbol}
              />
            </section>
            <section className="panel span-4">
              <TopIdeasPanel ideas={state?.signals ?? []} onRefresh={session.refreshNews} />
            </section>
            <section className="panel span-4">
              <MetricsPanel metrics={state?.metrics} />
            </section>
            <section className="panel span-4">
              <OrderBook
                symbol={selectedSymbol}
                book={state?.order_books?.[selectedSymbol]}
              />
            </section>
            <section className="panel span-5">
              <StrategyControls
                strategies={state?.strategies ?? {}}
                selectedSymbol={selectedSymbol}
                session={session}
              />
            </section>
            <section className="panel span-3">
              <RiskPanel risk={state?.risk} onToggleKillSwitch={session.toggleKillSwitch} />
            </section>
            <section className="panel span-4">
              <NewsFeedPanel articles={state?.news ?? []} />
            </section>
            <section className="panel span-4">
              <PortfolioPanel portfolio={state?.portfolio} />
            </section>
            <section className="panel span-7 tall">
              <Blotter orders={state?.orders ?? []} fills={state?.fills ?? []} />
            </section>
            <section className="panel span-5 tall">
              <LogsPanel logs={state?.logs ?? []} />
            </section>
          </main>
          </>}
        </>
      )}
    </div>
  );
}

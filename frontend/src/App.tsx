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
import ThreeBackground from "./components/ThreeBackground";
import LoginPage from "./components/LoginPage";
import GuidePanel from "./components/GuidePanel";
import { useMarketStream } from "./hooks/useMarketStream";
import { useSessionState } from "./hooks/useSessionState";

export default function App() {
  const { state, connected } = useMarketStream();
  const session = useSessionState(state);
  const selectedSymbol = session.selectedSymbol;
  const [entered, setEntered] = useState(() => window.sessionStorage.getItem("tradepulse.entered") === "1");

  const handleEnter = () => {
    window.sessionStorage.setItem("tradepulse.entered", "1");
    setEntered(true);
  };

  const handleLogout = () => {
    window.sessionStorage.removeItem("tradepulse.entered");
    setEntered(false);
  };

  return (
    <div className="app-shell">
      <ThreeBackground />
      {!entered ? (
        <LoginPage onEnter={handleEnter} />
      ) : (
        <>
          <Header connected={connected} state={state} session={session} onLogout={handleLogout} />
          {!connected && (
            <section className="connection-banner" role="status">
              <strong>Backend not connected.</strong>
              <span>Start the backend in another terminal, then refresh this page. The dashboard will load sample market data automatically.</span>
            </section>
          )}
          <GuidePanel
            connected={connected}
            marketRunning={Boolean(state?.session.market_running)}
            selectedSymbol={selectedSymbol}
            hasIdeas={Boolean(state?.signals.length)}
            onStart={() => session.startMarket(1)}
          />
          <main className="dashboard-grid">
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
        </>
      )}
    </div>
  );
}

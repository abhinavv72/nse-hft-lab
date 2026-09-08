interface GuidePanelProps {
  connected: boolean;
  marketRunning: boolean;
  selectedSymbol: string;
  hasIdeas: boolean;
  onStart: () => Promise<void>;
}

export default function GuidePanel({ connected, marketRunning, selectedSymbol, hasIdeas, onStart }: GuidePanelProps) {
  return (
    <section className="guide-panel" aria-label="How to use the simulator">
      <div className="guide-intro">
        <p className="eyebrow">QUICK START</p>
        <h2>Explore the market in four steps</h2>
        <p>Use this workspace to research simulated NSE market signals. It does not place real trades.</p>
      </div>
      <ol className="guide-steps">
        <li className={connected ? "complete" : "active"}>
          <span>1</span><div><strong>Connect</strong><small>{connected ? "Dashboard connected" : "Start the backend first"}</small></div>
        </li>
        <li className={marketRunning ? "complete" : connected ? "active" : ""}>
          <span>2</span><div><strong>Start simulation</strong><small>{marketRunning ? "Market replay is running" : "Load the sample market"}</small></div>
          <button disabled={!connected || marketRunning} onClick={() => void onStart()}>{marketRunning ? "Running" : "Start demo"}</button>
        </li>
        <li className={marketRunning ? "active" : ""}>
          <span>3</span><div><strong>Pick a stock</strong><small>Selected: {selectedSymbol}</small></div>
        </li>
        <li className={hasIdeas ? "complete" : marketRunning ? "active" : ""}>
          <span>4</span><div><strong>Review AI signals</strong><small>{hasIdeas ? "Ranked ideas are ready" : "Refresh news for ranked ideas"}</small></div>
        </li>
      </ol>
    </section>
  );
}

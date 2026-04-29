import type { SignalIdea } from "../types";

interface TopIdeasPanelProps {
  ideas: SignalIdea[];
  onRefresh: () => Promise<void>;
}

function scoreClass(bias: SignalIdea["bias"]) {
  if (bias === "bullish") return "buy-text";
  if (bias === "bearish") return "sell-text";
  return "";
}

export default function TopIdeasPanel({ ideas, onRefresh }: TopIdeasPanelProps) {
  const ranked = ideas.slice(0, 6);
  return (
    <div>
      <div className="panel-header">
        <div>
          <h2>Top Ideas</h2>
          <span className="subtle">Bullish and bearish bias for today</span>
        </div>
        <button className="muted" onClick={() => onRefresh()}>Refresh News</button>
      </div>
      <div className="stack">
        {ranked.map((idea) => (
          <div className="idea-card" key={idea.signal_id}>
            <div className="row">
              <strong>{idea.symbol}</strong>
              <strong className={scoreClass(idea.bias)}>{idea.bias.toUpperCase()}</strong>
            </div>
            <div className="row">
              <span>Confidence {idea.confidence}%</span>
              <span>Score {idea.score.toFixed(1)}</span>
              <span>{idea.change_pct ?? 0}%</span>
            </div>
            <div className="tag-row">
              {idea.reasons.slice(0, 3).map((reason) => (
                <span className="chip" key={reason}>{reason}</span>
              ))}
            </div>
            {idea.risks.length > 0 && (
              <p className="subtle">Risk: {idea.risks.join(", ")}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

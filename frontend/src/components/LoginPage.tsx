import type { CSSProperties, MouseEvent } from "react";
import { useState } from "react";

interface LoginPageProps {
  onEnter: () => void;
}

export default function LoginPage({ onEnter }: LoginPageProps) {
  const [style, setStyle] = useState<CSSProperties>({
    "--card-x": "0deg",
    "--card-y": "0deg",
    "--glow-x": "50%",
    "--glow-y": "50%",
  } as CSSProperties);

  const handleMove = (event: MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width;
    const py = (event.clientY - rect.top) / rect.height;
    setStyle({
      "--card-x": `${(0.5 - py) * 10}deg`,
      "--card-y": `${(px - 0.5) * 14}deg`,
      "--glow-x": `${px * 100}%`,
      "--glow-y": `${py * 100}%`,
    } as CSSProperties);
  };

  const resetMove = () => {
    setStyle({
      "--card-x": "0deg",
      "--card-y": "0deg",
      "--glow-x": "50%",
      "--glow-y": "50%",
    } as CSSProperties);
  };

  return (
    <div className="stitch-login-shell">
      <div className="stitch-bg-mesh" />
      <div
        className="stitch-login-card"
        onMouseMove={handleMove}
        onMouseLeave={resetMove}
        style={style}
      >
        <div className="stitch-card-glow" />
        <div className="stitch-card-chrome stitch-card-chrome-a" />
        <div className="stitch-card-chrome stitch-card-chrome-b" />

        <div className="stitch-card-content">
          <div className="stitch-topline">
            <span className="stitch-logo-icon">*</span>
            <span className="stitch-brand">TradeStock Pulse</span>
            <span className="stitch-badge">Intelligence</span>
          </div>

          <div className="stitch-copy">
            <h1>Read the market with depth.</h1>
            <p className="stitch-subtle">
              A premium Indian-market workspace combining live market context, mapped news,
              and explainable bullish or bearish signals.
            </p>
          </div>

          <div className="stitch-features">
            <div className="stitch-feature">
              <div className="stitch-feature-icon">01</div>
              <span>Live market pulse with ranked ideas</span>
            </div>
            <div className="stitch-feature">
              <div className="stitch-feature-icon">02</div>
              <span>News-linked bullish and bearish bias</span>
            </div>
            <div className="stitch-feature">
              <div className="stitch-feature-icon">03</div>
              <span>Simulation, risk, blotter, and order book</span>
            </div>
          </div>

          <div className="stitch-actions">
            <button className="stitch-enter-button" onClick={onEnter}>
              <span className="stitch-button-glow" />
              <span className="stitch-button-text">Launch Workspace</span>
            </button>
            <span className="stitch-subtext">Public demo environment — simulated trading only</span>
          </div>
        </div>
      </div>
    </div>
  );
}

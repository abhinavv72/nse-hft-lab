export type Side = "BUY" | "SELL";
export type OrderType = "LIMIT" | "MARKET";
export type OrderStatus = "ACCEPTED" | "PARTIAL" | "FILLED" | "CANCELLED" | "REJECTED";

export interface DepthLevel {
  price: number;
  qty: number;
}

export interface BookSnapshot {
  symbol: string;
  bids: DepthLevel[];
  asks: DepthLevel[];
  best_bid: number | null;
  best_ask: number | null;
  timestamp: string;
}

export interface MarketTick {
  timestamp: string;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number;
  last_price: number;
  mid_price: number;
  spread: number;
  volatility: number;
}

export interface OrderRecord {
  order_id: string;
  symbol: string;
  side: Side;
  order_type: OrderType;
  price: number;
  qty: number;
  remaining_qty: number;
  filled_qty: number;
  status: OrderStatus;
  owner: string;
  strategy_id?: string | null;
  timestamp: string;
  latency_ms?: number | null;
  reject_reason?: string | null;
}

export interface TradeRecord {
  trade_id: string;
  symbol: string;
  price: number;
  qty: number;
  taker_order_id: string;
  maker_order_id: string;
  aggressor_side: Side;
  timestamp: string;
}

export interface StrategyConfig {
  strategy_id: string;
  kind: "market_maker" | "mean_reversion";
  symbol: string;
  enabled: boolean;
  spread_bps: number;
  qty: number;
  aggression: number;
  threshold_bps: number;
  window: number;
}

export interface StrategyState {
  strategy_id: string;
  kind: StrategyConfig["kind"];
  symbol: string;
  enabled: boolean;
  config: StrategyConfig;
  outstanding_orders: string[];
  last_action?: string | null;
}

export interface RiskState {
  kill_switch_enabled: boolean;
  max_order_qty: number;
  max_position_per_symbol: number;
  max_daily_loss: number;
  max_price_deviation_bps: number;
  stale_market_ms: number;
  last_rejections: Array<Record<string, unknown>>;
}

export interface PositionSnapshot {
  symbol: string;
  net_qty: number;
  avg_price: number;
  realized_pnl: number;
  unrealized_pnl: number;
  mark_price: number;
  trade_count: number;
  fill_ratio: number;
}

export interface PortfolioSnapshot {
  positions: PositionSnapshot[];
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  total_trades: number;
}

export interface MetricsSnapshot {
  decision_latency_ms: Record<string, number>;
  round_trip_latency_ms: Record<string, number>;
  events_per_sec: number;
  fills_per_sec: number;
  total_trades: number;
  inventories: Record<string, number>;
}

export interface LogEvent {
  timestamp: string;
  level: string;
  category: string;
  message: string;
  data: Record<string, unknown>;
}

export interface NewsArticle {
  article_id: string;
  timestamp: string;
  source: string;
  headline: string;
  summary: string;
  url: string;
  symbols: string[];
  sentiment: "positive" | "negative" | "neutral";
  impact_score: number;
  tags: string[];
  analysis_source: "rules" | "finbert";
}

export interface SignalIdea {
  signal_id: string;
  symbol: string;
  bias: "bullish" | "bearish" | "neutral";
  confidence: number;
  score: number;
  horizon: string;
  last_price?: number | null;
  change_pct?: number | null;
  reasons: string[];
  risks: string[];
  related_articles: string[];
  timestamp: string;
}

export interface IpoIssue {
  company_name: string;
  symbol: string;
  series: string;
  status: string;
  open_date: string | null;
  close_date: string | null;
  price_band: string;
  issue_size_shares: string | number | null;
  subscription_times: number | null;
  shares_bid: string | number | null;
  shares_offered: string | number | null;
  official_url: string;
  lot_size: number | null;
  gmp: number | null;
  gmp_updated_at: string | null;
  gmp_source: string | null;
  retail_subscription: string | number | null;
  registrar: string | null;
}

export interface SessionState {
  session_id: string;
  mode: "live" | "replay" | "paused";
  market_running: boolean;
  replay_running: boolean;
  speed: number;
  selected_symbol: string;
  deterministic_seed: number;
}

export interface DashboardState {
  session: SessionState;
  market: Record<string, MarketTick>;
  order_books: Record<string, BookSnapshot>;
  strategies: Record<string, StrategyState>;
  orders: OrderRecord[];
  fills: TradeRecord[];
  risk: RiskState;
  portfolio: PortfolioSnapshot;
  metrics: MetricsSnapshot;
  news: NewsArticle[];
  signals: SignalIdea[];
  logs: LogEvent[];
}

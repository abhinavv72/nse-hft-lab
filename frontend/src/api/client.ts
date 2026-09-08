// Production serves the UI and API from the same origin. Vite development
// still runs the UI on 5173 and the API on 8000.
const localApiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? localApiBase : "")).replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getState: () => request("/api/market/state"),
  getCurrentIpos: () => request<{ source: string; cached: boolean; issues: import("../types").IpoIssue[] }>("/api/market/ipo/current"),
  startMarket: (speed: number, mode = "live") => request("/api/market/start", { method: "POST", body: JSON.stringify({ speed, mode }) }),
  stopMarket: () => request("/api/market/stop", { method: "POST" }),
  resetMarket: () => request("/api/market/reset", { method: "POST" }),
  injectVolatility: () => request("/api/market/volatility-spike", { method: "POST" }),
  selectSymbol: (symbol: string) => request("/api/market/select-symbol", { method: "POST", body: JSON.stringify({ symbol }) }),
  listStrategies: () => request("/api/strategy"),
  startStrategy: (strategyId: string, payload: Record<string, unknown>) =>
    request(`/api/strategy/start/${strategyId}`, { method: "POST", body: JSON.stringify(payload) }),
  stopStrategy: (strategyId: string) => request(`/api/strategy/stop/${strategyId}`, { method: "POST" }),
  updateStrategy: (strategyId: string, payload: Record<string, unknown>) =>
    request(`/api/strategy/config/${strategyId}`, { method: "POST", body: JSON.stringify(payload) }),
  getRisk: () => request("/api/risk"),
  setKillSwitch: (enabled: boolean) => request("/api/risk/kill-switch", { method: "POST", body: JSON.stringify({ enabled }) }),
  updateLimits: (payload: Record<string, unknown>) => request("/api/risk/limits", { method: "POST", body: JSON.stringify(payload) }),
  getPortfolio: () => request("/api/portfolio"),
  getMetrics: () => request("/api/metrics"),
  getNews: () => request("/api/news"),
  refreshNews: () => request("/api/news/refresh", { method: "POST" }),
  getSignals: () => request("/api/signals"),
  listReplaySessions: () => request<{ sessions: string[] }>("/api/replay/sessions"),
  startReplay: (sessionId: string, speed: number) =>
    request("/api/replay/start", { method: "POST", body: JSON.stringify({ session_id: sessionId, speed }) }),
  exportSession: () => request("/api/replay/export", { method: "POST" }),
};

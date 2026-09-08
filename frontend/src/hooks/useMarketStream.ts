import { useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import { connectDashboard } from "../api/ws";
import type { DashboardState, MarketTick } from "../types";

export type MarketHistory = Record<string, MarketTick[]>;

export function useMarketStream() {
  const [state, setState] = useState<DashboardState | null>(null);
  const [connected, setConnected] = useState(false);
  const [history, setHistory] = useState<MarketHistory>({});
  const lastUpdateAt = useRef(0);

  useEffect(() => {
    let cancelled = false;

    const loadState = async () => {
      try {
        const snapshot = await api.getState();
        if (!cancelled) {
          setState(snapshot as DashboardState);
        }
      } catch {
        // keep last known state
      }
    };

    loadState();

    let socketConnected = false;
    const handle = connectDashboard(
      (payload) => {
        const message = payload as { type?: string; data?: DashboardState };
        if (message.type === "dashboard" && message.data) {
          const dashboard = message.data;
          socketConnected = true;
          // A full dashboard re-render is expensive. The UI only needs a smooth
          // snapshot a few times a second, not every engine event.
          if (Date.now() - lastUpdateAt.current > 400) {
            lastUpdateAt.current = Date.now();
            setState(dashboard);
            setHistory((current) => {
              const next = { ...current };
              for (const [symbol, tick] of Object.entries(dashboard.market)) {
                next[symbol] = [...(current[symbol] ?? []), tick].slice(-48);
              }
              return next;
            });
          }
          setConnected(true);
        }
      },
      () => {
        socketConnected = false;
        setConnected(false);
      },
    );

    const poll = window.setInterval(() => {
      if (!socketConnected) {
        loadState();
      }
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(poll);
      setConnected(false);
      handle.close();
    };
  }, []);

  return { state, connected, history };
}

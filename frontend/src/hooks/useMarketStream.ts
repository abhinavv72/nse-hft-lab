import { useEffect, useState } from "react";

import { api } from "../api/client";
import { connectDashboard } from "../api/ws";
import type { DashboardState } from "../types";

export function useMarketStream() {
  const [state, setState] = useState<DashboardState | null>(null);
  const [connected, setConnected] = useState(false);

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

    const handle = connectDashboard(
      (payload) => {
        const message = payload as { type?: string; data?: DashboardState };
        if (message.type === "dashboard" && message.data) {
          setState(message.data);
          setConnected(true);
        }
      },
      () => setConnected(false),
    );

    const poll = window.setInterval(() => {
      if (!connected) {
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

  return { state, connected };
}

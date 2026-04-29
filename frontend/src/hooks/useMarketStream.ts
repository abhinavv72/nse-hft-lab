import { useEffect, useState } from "react";

import { api } from "../api/client";
import { connectDashboard } from "../api/ws";
import type { DashboardState } from "../types";

export function useMarketStream() {
  const [state, setState] = useState<DashboardState | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    api.getState().then((snapshot) => setState(snapshot as DashboardState)).catch(() => undefined);
    const socket = connectDashboard((payload) => {
      const message = payload as { type?: string; data?: DashboardState };
      if (message.type === "dashboard" && message.data) {
        setState(message.data);
        setConnected(true);
      }
    });
    socket.onclose = () => setConnected(false);
    return () => socket.close();
  }, []);

  return { state, connected };
}

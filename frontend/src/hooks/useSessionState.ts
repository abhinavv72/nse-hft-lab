import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { DashboardState, StrategyState } from "../types";

export function useSessionState(state: DashboardState | null) {
  const [selectedSymbol, setSelectedSymbol] = useState("NIFTY");
  const [replaySessions, setReplaySessions] = useState<string[]>([]);
  const [strategyDrafts, setStrategyDrafts] = useState<Record<string, Partial<StrategyState["config"]>>>({});

  useEffect(() => {
    if (state?.session.selected_symbol) {
      setSelectedSymbol(state.session.selected_symbol);
    }
  }, [state?.session.selected_symbol]);

  useEffect(() => {
    api.listReplaySessions()
      .then((response) => setReplaySessions(response.sessions))
      .catch(() => undefined);
  }, []);

  async function selectSymbol(symbol: string) {
    setSelectedSymbol(symbol);
    await api.selectSymbol(symbol);
  }

  async function startMarket(speed: number) {
    await api.startMarket(speed, "live");
  }

  async function stopMarket() {
    await api.stopMarket();
  }

  async function resetMarket() {
    await api.resetMarket();
  }

  async function injectVolatility() {
    await api.injectVolatility();
  }

  async function toggleKillSwitch(enabled: boolean) {
    await api.setKillSwitch(enabled);
  }

  async function exportSession() {
    await api.exportSession();
  }

  async function refreshNews() {
    await api.refreshNews();
  }

  async function startReplay(sessionId: string, speed: number) {
    await api.startReplay(sessionId, speed);
  }

  async function startStrategy(strategyId: string, payload: Record<string, unknown>) {
    await api.startStrategy(strategyId, payload);
  }

  async function stopStrategy(strategyId: string) {
    await api.stopStrategy(strategyId);
  }

  function updateDraft(strategyId: string, patch: Partial<StrategyState["config"]>) {
    setStrategyDrafts((current) => ({
      ...current,
      [strategyId]: { ...current[strategyId], ...patch },
    }));
  }

  return {
    selectedSymbol,
    replaySessions,
    strategyDrafts,
    setSelectedSymbol: selectSymbol,
    startMarket,
    stopMarket,
    resetMarket,
    injectVolatility,
    toggleKillSwitch,
    exportSession,
    refreshNews,
    startReplay,
    startStrategy,
    stopStrategy,
    updateDraft,
  };
}

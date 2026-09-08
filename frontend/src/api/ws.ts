const RECONNECT_DELAYS = [1000, 2000, 5000, 10000]; // ms

export function connectDashboard(
  onMessage: (payload: unknown) => void,
  onClose?: () => void,
): { close: () => void } {
  const configuredBase = (import.meta.env.VITE_WS_BASE_URL ?? "").replace(/\/$/, "");
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const localWsBase = `${protocol}//${window.location.hostname}:8000`;
  const base = configuredBase || (import.meta.env.DEV ? localWsBase : `${protocol}//${window.location.host}`);
  const url = `${base}/ws`;

  let socket: WebSocket;
  let attempt = 0;
  let stopped = false;

  function connect() {
    socket = new WebSocket(url);

    socket.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data));
        attempt = 0; // reset backoff on successful message
      } catch {
        // ignore malformed frames
      }
    };

    socket.onclose = () => {
      onClose?.();
      if (stopped) return;
      const delay = RECONNECT_DELAYS[Math.min(attempt, RECONNECT_DELAYS.length - 1)];
      attempt++;
      setTimeout(connect, delay);
    };

    socket.onerror = () => {
      // onclose will fire next and handle reconnect
    };
  }

  connect();

  return {
    close() {
      stopped = true;
      socket?.close();
    },
  };
}

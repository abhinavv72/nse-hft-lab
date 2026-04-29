export function connectDashboard(onMessage: (payload: unknown) => void): WebSocket {
  const browserHost = window.location.hostname || "localhost";
  const socket = new WebSocket(`ws://${browserHost}:8000/ws`);
  socket.onmessage = (event) => {
    onMessage(JSON.parse(event.data));
  };
  return socket;
}

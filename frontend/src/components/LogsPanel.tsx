import type { LogEvent } from "../types";

interface LogsPanelProps {
  logs: LogEvent[];
}

export default function LogsPanel({ logs }: LogsPanelProps) {
  return (
    <div>
      <div className="panel-header">
        <h2>Logs</h2>
        <span>{logs.length} events</span>
      </div>
      <div className="stack tight">
        {logs.length === 0 && <p className="empty-state">System activity will be recorded here once the simulation starts.</p>}
        {logs.slice(0, 16).map((log, index) => (
          <div className="log-row" key={`${log.timestamp}-${index}`}>
            <span>{log.timestamp.split("T")[1]?.replace("Z", "")}</span>
            <strong>{log.level}</strong>
            <span>{log.category}</span>
            <span>{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

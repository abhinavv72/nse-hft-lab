import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles/theme.css";

class ErrorBoundary extends React.Component<
  React.PropsWithChildren,
  { hasError: boolean; message: string }
> {
  constructor(props: React.PropsWithChildren) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, message: error.message || "Unknown frontend error" };
  }

  override componentDidCatch(error: Error) {
    console.error("frontend-crash", error);
  }

  override render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "24px", color: "#e6f1ff", background: "#08111d", minHeight: "100vh" }}>
          <h2>Frontend Error</h2>
          <p>{this.state.message}</p>
          <p>Open browser console for the full stack trace.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);

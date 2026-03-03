import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import LoginPage from "./LoginPage";
import { useAuth } from "./hooks/useAuth";
import "./index.css";

function FullScreenSpinner() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <span className="inline-block w-8 h-8 border-2 border-gray-700 border-t-purple-500 rounded-full animate-spin" />
    </div>
  );
}

function Root() {
  const { status } = useAuth();
  if (status === "pending") return <FullScreenSpinner />;
  if (status === "unauthenticated") return <LoginPage />;
  return <App />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);

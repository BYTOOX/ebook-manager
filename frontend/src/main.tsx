import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./providers/AuthProvider";
import { ThemeProvider } from "./providers/ThemeProvider";
import { OfflineProvider } from "./providers/OfflineProvider";
import { SyncProvider } from "./providers/SyncProvider";
import "./styles/global.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1
    }
  }
});

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <OfflineProvider>
          <AuthProvider>
            <SyncProvider>
              <BrowserRouter>
                <App />
              </BrowserRouter>
            </SyncProvider>
          </AuthProvider>
        </OfflineProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);

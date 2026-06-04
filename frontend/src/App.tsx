import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { ThemeToggle } from "./components/ThemeToggle/ThemeToggle";
import { Dashboard } from "./pages/Dashboard";
import { AuditTrail } from "./pages/AuditTrail";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-indigo-600 focus:px-3 focus:py-2 focus:text-white"
        >
          Skip to content
        </a>
        <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-900 dark:text-slate-100">
          <header className="border-b bg-white dark:border-slate-700 dark:bg-slate-800">
            <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3" aria-label="Main">
              <Link to="/" className="text-lg font-bold">
                Chronos
              </Link>
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-500 dark:text-slate-400">invest-agent</span>
                <ThemeToggle />
              </div>
            </nav>
          </header>
          <main id="main" className="mx-auto max-w-6xl px-4 py-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/audit/:id" element={<AuditTrail />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

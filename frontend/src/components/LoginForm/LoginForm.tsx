import { FormEvent, useState } from "react";
import { useAuth } from "../../hooks/useAuth";

export function LoginForm() {
  const { login } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
    } catch {
      setError("Login failed. Check credentials.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
        className="rounded border px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-700"
        aria-label="Username"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        className="rounded border px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-700"
        aria-label="Password"
      />
      <button
        type="submit"
        disabled={busy}
        className="rounded bg-indigo-600 px-3 py-1 text-sm text-white disabled:opacity-50"
      >
        {busy ? "..." : "Login"}
      </button>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </form>
  );
}

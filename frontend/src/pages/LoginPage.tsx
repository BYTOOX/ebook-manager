import { FormEvent, useState } from "react";
import { Lock, LogIn, UserPlus } from "lucide-react";
import { useAuth } from "../providers/AuthProvider";
import { BrandLogo } from "../components/BrandLogo";

export function LoginPage() {
  const { login, setup } = useAuth();
  const [mode, setMode] = useState<"login" | "setup">("login");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("Aurelia");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "setup") {
        await setup(username, password, displayName);
      } else {
        await login(username, password);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Erreur inconnue");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-panel">
        <BrandLogo variant="small" className="login-logo" label="Aurelia EPUB Reader" />
        <h1 className="sr-only">Aurelia</h1>
        <p>Bibliotheque EPUB personnelle.</p>

        <div className="segmented" role="tablist" aria-label="Mode auth">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            <LogIn size={16} aria-hidden="true" />
            Connexion
          </button>
          <button className={mode === "setup" ? "active" : ""} onClick={() => setMode("setup")}>
            <UserPlus size={16} aria-hidden="true" />
            Setup
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            <span>Utilisateur</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          {mode === "setup" && (
            <label>
              <span>Nom affiche</span>
              <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
          )}
          <label>
            <span>Mot de passe</span>
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete={mode === "setup" ? "new-password" : "current-password"}
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button className="primary-action wide" type="submit" disabled={busy}>
            <Lock size={18} aria-hidden="true" />
            {busy ? "..." : mode === "setup" ? "Creer admin" : "Entrer"}
          </button>
        </form>
      </section>
    </main>
  );
}

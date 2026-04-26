import { LogOut, Moon, Settings2, Upload } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../providers/AuthProvider";
import { useUiStore, type AppTheme } from "../stores/ui";

const themes: AppTheme[] = ["system", "black_gold", "dark", "light"];

export function SettingsPage() {
  const { logout } = useAuth();
  const theme = useUiStore((state) => state.theme);
  const setTheme = useUiStore((state) => state.setTheme);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Aurelia</p>
          <h1>Settings</h1>
        </div>
      </header>

      <section className="settings-section">
        <h2>Apparence</h2>
        <div className="theme-grid">
          {themes.map((item) => (
            <button key={item} className={theme === item ? "active" : ""} onClick={() => setTheme(item)}>
              <Moon size={17} aria-hidden="true" />
              {item}
            </button>
          ))}
        </div>
      </section>

      <section className="settings-section">
        <h2>Gestion</h2>
        <Link className="settings-link" to="/import">
          <Upload size={19} aria-hidden="true" />
          Import EPUB
        </Link>
        <Link className="settings-link" to="/settings/advanced">
          <Settings2 size={19} aria-hidden="true" />
          Avance
        </Link>
      </section>

      <button className="secondary-action wide" onClick={() => void logout()}>
        <LogOut size={18} aria-hidden="true" />
        Logout
      </button>
    </main>
  );
}

export function AdvancedSettingsPage() {
  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Gestion</p>
          <h1>Avance</h1>
        </div>
      </header>
      <section className="quiet-panel">
        <h2>Socle Phase 1</h2>
        <p>Imports, scan, logs et metadata providers seront branches dans les phases suivantes.</p>
      </section>
    </main>
  );
}

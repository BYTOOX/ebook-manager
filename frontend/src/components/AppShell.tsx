import { BookOpen, Home, Library, Search, Settings, Sparkles } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { useSyncState } from "../providers/SyncProvider";
import { useAuth } from "../providers/AuthProvider";
import type { ReactNode } from "react";
import { BrandLogo } from "./BrandLogo";

const navItems = [
  { to: "/", label: "Home", icon: Home },
  { to: "/library", label: "Library", icon: Library },
  { to: "/search", label: "Search", icon: Search },
  { to: "/collections", label: "Collections", icon: BookOpen },
  { to: "/settings", label: "Settings", icon: Settings }
];

export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const { state } = useSyncState();
  const { user } = useAuth();
  const hideNav = location.pathname.startsWith("/reader");

  return (
    <div className={hideNav ? "app-shell reader-shell" : "app-shell"}>
      {!hideNav && (
        <header className="topbar">
          <NavLink to="/" className="topbar-brand" aria-label="Aurelia home">
            <BrandLogo variant="full" className="topbar-logo" label="Aurelia" />
          </NavLink>
          <div className="topbar-status" title={`Sync: ${state}`}>
            <Sparkles size={15} aria-hidden="true" />
            <span>{state}</span>
          </div>
          <span className="avatar" title={user?.display_name ?? user?.username ?? "Aurelia"}>
            {(user?.display_name ?? user?.username ?? "A").slice(0, 1).toUpperCase()}
          </span>
        </header>
      )}
      <div className="app-content">{children}</div>
      {!hideNav && (
        <nav className="bottom-nav" aria-label="Navigation principale">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
            >
              <item.icon size={20} aria-hidden="true" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  );
}

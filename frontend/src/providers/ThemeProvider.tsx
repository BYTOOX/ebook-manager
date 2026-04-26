import { useEffect, type ReactNode } from "react";
import { useUiStore } from "../stores/ui";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme = useUiStore((state) => state.theme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  return <>{children}</>;
}

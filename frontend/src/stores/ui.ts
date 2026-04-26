import { create } from "zustand";

export type AppTheme = "system" | "dark" | "light" | "black_gold";

type UiState = {
  theme: AppTheme;
  setTheme: (theme: AppTheme) => void;
};

export const useUiStore = create<UiState>((set) => ({
  theme: "black_gold",
  setTheme: (theme) => set({ theme })
}));

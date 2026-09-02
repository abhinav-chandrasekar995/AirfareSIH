"use client";
import { create } from "zustand";

type Theme = "dark" | "light";

interface UiState {
  theme: Theme;
  sidebarCollapsed: boolean;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  toggleSidebar: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  theme: "dark",
  sidebarCollapsed: false,
  setTheme: (theme) => {
    if (typeof document !== "undefined") document.documentElement.setAttribute("data-theme", theme);
    set({ theme });
  },
  toggleTheme: () =>
    set((state) => {
      const theme = state.theme === "dark" ? "light" : "dark";
      if (typeof document !== "undefined") document.documentElement.setAttribute("data-theme", theme);
      return { theme };
    }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}));

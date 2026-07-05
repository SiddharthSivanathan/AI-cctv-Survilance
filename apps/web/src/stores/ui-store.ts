import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UiState {
  soundEnabled: boolean;
  browserNotifications: boolean;
  setSoundEnabled: (enabled: boolean) => void;
  setBrowserNotifications: (enabled: boolean) => void;
}

/** Small persisted UI preferences (alert sound, browser notifications). */
export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      soundEnabled: true,
      browserNotifications: false,
      setSoundEnabled: (enabled) => set({ soundEnabled: enabled }),
      setBrowserNotifications: (enabled) => set({ browserNotifications: enabled }),
    }),
    { name: 'visionops-ui' },
  ),
);

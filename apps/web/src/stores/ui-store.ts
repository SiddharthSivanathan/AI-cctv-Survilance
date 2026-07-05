import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UiState {
  soundEnabled: boolean;
  setSoundEnabled: (enabled: boolean) => void;
}

/** Small persisted UI preferences (e.g. alert sound). */
export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      soundEnabled: true,
      setSoundEnabled: (enabled) => set({ soundEnabled: enabled }),
    }),
    { name: 'visionops-ui' },
  ),
);

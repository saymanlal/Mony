import { create } from 'zustand';

export type OperatingMode = 'automated' | 'manual';
export type FiatCurrency = 'INR' | 'USD';

interface SettingsState {
  mode: OperatingMode;
  currency: FiatCurrency;
  biometricEnabled: boolean;
  lockTimeoutMinutes: number;
  reduceMotion: boolean;
  setMode: (mode: OperatingMode) => void;
  setCurrency: (currency: FiatCurrency) => void;
  setBiometricEnabled: (enabled: boolean) => void;
  setLockTimeoutMinutes: (minutes: number) => void;
  setReduceMotion: (reduce: boolean) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  mode: 'automated',
  currency: 'INR',
  biometricEnabled: true,
  lockTimeoutMinutes: 5,
  reduceMotion: false,
  setMode: (mode) => set({ mode }),
  setCurrency: (currency) => set({ currency }),
  setBiometricEnabled: (biometricEnabled) => set({ biometricEnabled }),
  setLockTimeoutMinutes: (lockTimeoutMinutes) => set({ lockTimeoutMinutes }),
  setReduceMotion: (reduceMotion) => set({ reduceMotion }),
}));

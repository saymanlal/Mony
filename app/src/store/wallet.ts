import { create } from 'zustand';

interface WalletState {
  address: string | null;
  isUnlocked: boolean;
  hasBackedUpPhrase: boolean;
  monBalance: string;
  inrValue: number;
  setAddress: (address: string | null) => void;
  setUnlocked: (unlocked: boolean) => void;
  setHasBackedUpPhrase: (backedUp: boolean) => void;
  setBalances: (monBalance: string, inrValue: number) => void;
  clearWallet: () => void;
}

export const useWalletStore = create<WalletState>((set) => ({
  address: null,
  isUnlocked: false,
  hasBackedUpPhrase: false,
  monBalance: '0.0000',
  inrValue: 0.0,
  setAddress: (address) => set({ address }),
  setUnlocked: (isUnlocked) => set({ isUnlocked }),
  setHasBackedUpPhrase: (hasBackedUpPhrase) => set({ hasBackedUpPhrase }),
  setBalances: (monBalance, inrValue) => set({ monBalance, inrValue }),
  clearWallet: () =>
    set({
      address: null,
      isUnlocked: false,
      hasBackedUpPhrase: false,
      monBalance: '0.0000',
      inrValue: 0.0,
    }),
}));

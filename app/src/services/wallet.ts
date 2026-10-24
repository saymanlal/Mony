/**
 * Embedded wallet management and cryptographic signing via viem and expo-secure-store.
 */

import * as SecureStore from 'expo-secure-store';
import { createWalletClient, http, custom } from 'viem';
import { privateKeyToAccount, generateMnemonic, mnemonicToAccount } from 'viem/accounts';

const SECURE_STORE_KEY = 'mony_wallet_mnemonic';
const BACKUP_QUIZ_STATUS_KEY = 'mony_backup_completed';

export const monadTestnet = {
  id: 10143,
  name: 'Monad Testnet',
  nativeCurrency: { name: 'MON', symbol: 'MON', decimals: 18 },
  rpcUrls: {
    default: { http: [process.env.EXPO_PUBLIC_MONAD_RPC || 'https://testnet-rpc.monad.xyz'] },
  },
  blockExplorers: {
    default: { name: 'Monad Explorer', url: 'https://testnet.monadexplorer.com' },
  },
};

export class WalletService {
  /**
   * Create a new mnemonic wallet and securely persist it.
   */
  static async createWallet(): Promise<{ mnemonic: string; address: string }> {
    const mnemonic = generateMnemonic();
    const account = mnemonicToAccount(mnemonic);
    await SecureStore.setItemAsync(SECURE_STORE_KEY, mnemonic, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
    await SecureStore.setItemAsync(BACKUP_QUIZ_STATUS_KEY, 'false');
    return { mnemonic, address: account.address };
  }

  /**
   * Import wallet from existing mnemonic.
   */
  static async importWallet(mnemonic: string): Promise<string> {
    const clean = mnemonic.trim().toLowerCase();
    const account = mnemonicToAccount(clean);
    await SecureStore.setItemAsync(SECURE_STORE_KEY, clean, {
      keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
    await SecureStore.setItemAsync(BACKUP_QUIZ_STATUS_KEY, 'true');
    return account.address;
  }

  /**
   * Retrieve stored mnemonic.
   */
  static async getStoredMnemonic(): Promise<string | null> {
    return await SecureStore.getItemAsync(SECURE_STORE_KEY);
  }

  /**
   * Get public address of active wallet.
   */
  static async getActiveAddress(): Promise<string | null> {
    const mnemonic = await this.getStoredMnemonic();
    if (!mnemonic) return null;
    try {
      const account = mnemonicToAccount(mnemonic);
      return account.address;
    } catch {
      return null;
    }
  }

  /**
   * Sign EIP-712 DepositIntent for Manual Mode deposit releases.
   */
  static async signDepositIntent(params: {
    voucherHash: `0x${string}`;
    nonce: bigint;
    expiry: bigint;
    treasuryAddress: `0x${string}`;
    chainId: number;
  }): Promise<string> {
    const mnemonic = await this.getStoredMnemonic();
    if (!mnemonic) throw new Error('No wallet found');
    const account = mnemonicToAccount(mnemonic);

    const domain = {
      name: 'MonyTreasury',
      version: '1',
      chainId: BigInt(params.chainId),
      verifyingContract: params.treasuryAddress,
    };

    const types = {
      DepositIntent: [
        { name: 'voucherHash', type: 'bytes32' },
        { name: 'nonce', type: 'uint256' },
        { name: 'expiry', type: 'uint256' },
      ],
    };

    const signature = await account.signTypedData({
      domain,
      types,
      primaryType: 'DepositIntent',
      message: {
        voucherHash: params.voucherHash,
        nonce: params.nonce,
        expiry: params.expiry,
      },
    });

    return signature;
  }
}

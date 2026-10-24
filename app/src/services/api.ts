/**
 * Backend API client for MONY.
 */

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://mony-backend.onrender.com';

export interface ScanChallenge {
  nonce: string;
  issued_at_ms: number;
  expiry_ms: number;
  hmac_signature: string;
  session_id: string;
}

export interface VerificationResult {
  decision: 'ACCEPT' | 'REJECT' | 'RESCAN';
  score: number;
  reason_code: string;
  human_reason: string;
  user_hint?: string;
  voucher?: {
    user: string;
    amount_wei: string;
    amount_mon: number;
    denomination_inr: number;
    note_hash: string;
    nonce: number;
    expiry: number;
    signature: string;
  };
  breakdown: Record<string, any>;
}

export const api = {
  async getChallenge(): Promise<ScanChallenge> {
    const res = await fetch(`${API_BASE_URL}/v1/scan/challenge`, { method: 'POST' });
    if (!res.ok) throw new Error(`Challenge error: ${res.status}`);
    return res.json();
  },

  async verifyScan(formData: FormData): Promise<VerificationResult> {
    const res = await fetch(`${API_BASE_URL}/v1/scan/verify`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Scan verification failed' }));
      throw new Error(err.detail || 'Scan verification failed');
    }
    return res.json();
  },

  async getDepositQuote(denomination: number, userAddress: string) {
    const res = await fetch(
      `${API_BASE_URL}/v1/quote/deposit?denomination=${denomination}&user_address=${userAddress}`
    );
    if (!res.ok) throw new Error('Failed to fetch deposit quote');
    return res.json();
  },

  async releaseDeposit(params: {
    user_address: string;
    mode: 'automated' | 'manual';
    voucher: any;
    deposit_intent?: any;
    user_signature?: string;
  }) {
    const res = await fetch(`${API_BASE_URL}/v1/deposit/release`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Release failed' }));
      throw new Error(err.detail || 'Release failed');
    }
    return res.json();
  },

  async getExchangeQuote(params: {
    user_address: string;
    token_in: string;
    token_out: string;
    amount_in: string;
  }) {
    const res = await fetch(`${API_BASE_URL}/v1/exchange/quote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Exchange quote failed');
    return res.json();
  },

  async getAnalytics(userAddress: string) {
    const res = await fetch(`${API_BASE_URL}/v1/analytics/summary?user_address=${userAddress}`);
    if (!res.ok) throw new Error('Analytics failed');
    return res.json();
  },

  async getFiatRates() {
    const res = await fetch(`${API_BASE_URL}/v1/rates/fiat`);
    if (!res.ok) throw new Error('Rates failed');
    return res.json();
  },

  async createInvoice(params: any) {
    const res = await fetch(`${API_BASE_URL}/v1/invoices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Invoice creation failed');
    return res.json();
  },
};

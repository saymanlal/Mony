/**
 * EIP-681 standard QR code parser for Ethereum and EVM payments.
 * Format: ethereum:0x...[@chainId]?value=1e18
 */

export interface ParsedPaymentUri {
  targetAddress: string;
  chainId?: number;
  valueWei?: string;
  functionName?: string;
}

export function parseEIP681(uri: string): ParsedPaymentUri | null {
  if (!uri) return null;
  const cleanUri = uri.trim();

  // Plain address format
  if (/^0x[a-fA-F0-9]{40}$/.test(cleanUri)) {
    return {
      targetAddress: cleanUri,
    };
  }

  // EIP-681 URI format
  if (!cleanUri.toLowerCase().startsWith('ethereum:')) {
    return null;
  }

  try {
    const raw = cleanUri.substring('ethereum:'.length);
    const parts = raw.split('?');
    const addressPart = parts[0];
    const queryPart = parts[1] || '';

    // Handle @chainId in address
    let targetAddress = addressPart;
    let chainId: number | undefined;

    if (addressPart.includes('@')) {
      const [addr, chain] = addressPart.split('@');
      targetAddress = addr;
      chainId = parseInt(chain, 10);
    }

    if (!/^0x[a-fA-F0-9]{40}$/.test(targetAddress)) {
      return null;
    }

    const params = new URLSearchParams(queryPart);
    const valueWei = params.get('value') || undefined;

    return {
      targetAddress,
      chainId,
      valueWei,
    };
  } catch {
    return null;
  }
}

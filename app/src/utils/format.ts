/**
 * Formatting utilities for MONY.
 */

/**
 * Format INR with Indian digit grouping (e.g. 1,00,000 and 1,00,00,000).
 */
export function formatINR(amount: number): string {
  if (isNaN(amount)) return '0.00';
  const parts = amount.toFixed(2).split('.');
  let integerPart = parts[0];
  const decimalPart = parts[1];

  const isNegative = integerPart.startsWith('-');
  if (isNegative) {
    integerPart = integerPart.substring(1);
  }

  if (integerPart.length <= 3) {
    return (isNegative ? '-' : '') + integerPart + '.' + decimalPart;
  }

  const lastThree = integerPart.substring(integerPart.length - 3);
  const remaining = integerPart.substring(0, integerPart.length - 3);

  const formattedRemaining = remaining.replace(/\B(?=(\d{2})+(?!\d))/g, ',');
  const formatted = (isNegative ? '-' : '') + formattedRemaining + ',' + lastThree + '.' + decimalPart;
  return formatted;
}

/**
 * Format MON token amount with custom decimal precision.
 */
export function formatMON(amount: number | string, decimals: number = 4): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '0.0000';
  return num.toFixed(decimals);
}

/**
 * Truncate EVM wallet address consistently (0x1234...abcd).
 */
export function truncateAddress(address: string, startChars: number = 6, endChars: number = 4): string {
  if (!address || address.length < startChars + endChars) return address || '';
  return `${address.substring(0, startChars)}...${address.substring(address.length - endChars)}`;
}

/**
 * Truncate transaction hash.
 */
export function truncateHash(hash: string): string {
  return truncateAddress(hash, 8, 6);
}

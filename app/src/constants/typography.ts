export const Typography = {
  family: {
    interface: 'System', // Instrument Sans fallback
    balance: 'System',   // Instrument Serif fallback
    mono: 'monospace',   // JetBrains Mono fallback
  },
  size: {
    hero: 44,
    display: 34,
    title1: 24,
    title2: 20,
    headline: 17,
    body: 15,
    callout: 14,
    subhead: 13,
    footnote: 12,
    caption: 11,
  },
  weight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
};

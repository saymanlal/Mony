import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { formatINR, formatMON } from '../../utils/format';
import { Colors } from '../../constants/colors';

interface AmountDisplayProps {
  monAmount: number | string;
  inrAmount?: number;
  size?: 'normal' | 'large' | 'hero';
}

export const AmountDisplay: React.FC<AmountDisplayProps> = ({
  monAmount,
  inrAmount,
  size = 'normal',
}) => {
  const isHero = size === 'hero';
  const isLarge = size === 'large';

  return (
    <View style={styles.container}>
      <View style={styles.row}>
        <Text
          style={[
            styles.monText,
            isLarge && styles.monLarge,
            isHero && styles.monHero,
          ]}
        >
          {formatMON(monAmount)}
        </Text>
        <Text
          style={[
            styles.currencySymbol,
            isLarge && styles.symbolLarge,
            isHero && styles.symbolHero,
          ]}
        >
          MON
        </Text>
      </View>
      {inrAmount !== undefined && (
        <Text style={styles.fiatSubtext}>
          ₹{formatINR(inrAmount)}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  monText: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.light.ink,
    fontVariant: ['tabular-nums'],
  },
  monLarge: {
    fontSize: 34,
  },
  monHero: {
    fontSize: 44,
  },
  currencySymbol: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.secondaryText,
    marginLeft: 6,
  },
  symbolLarge: {
    fontSize: 18,
  },
  symbolHero: {
    fontSize: 22,
  },
  fiatSubtext: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.light.secondaryText,
    fontVariant: ['tabular-nums'],
    marginTop: 2,
  },
});

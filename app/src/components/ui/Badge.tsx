import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { Colors } from '../../constants/colors';

interface BadgeProps {
  label: string;
  variant?: 'neutral' | 'success' | 'caution' | 'error';
  style?: ViewStyle;
}

export const Badge: React.FC<BadgeProps> = ({ label, variant = 'neutral', style }) => {
  return (
    <View
      style={[
        styles.base,
        variant === 'neutral' && styles.neutral,
        variant === 'success' && styles.success,
        variant === 'caution' && styles.caution,
        variant === 'error' && styles.error,
        style,
      ]}
    >
      <Text
        style={[
          styles.text,
          variant === 'neutral' && styles.textNeutral,
          variant === 'success' && styles.textSuccess,
          variant === 'caution' && styles.textCaution,
          variant === 'error' && styles.textError,
        ]}
      >
        {label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  base: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  neutral: {
    backgroundColor: Colors.light.paper,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
  },
  success: {
    backgroundColor: Colors.light.primarySubtle,
  },
  caution: {
    backgroundColor: '#FEF3C7',
  },
  error: {
    backgroundColor: '#FEE2E2',
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  textNeutral: {
    color: Colors.light.secondaryText,
  },
  textSuccess: {
    color: Colors.light.primary,
  },
  textCaution: {
    color: Colors.light.caution,
  },
  textError: {
    color: Colors.light.error,
  },
});

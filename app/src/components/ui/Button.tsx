import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { Colors } from '../../constants/colors';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'destructive' | 'ghost';
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  style,
  textStyle,
}) => {
  const isPrimary = variant === 'primary';
  const isSecondary = variant === 'secondary';
  const isDestructive = variant === 'destructive';
  const isGhost = variant === 'ghost';

  return (
    <TouchableOpacity
      activeOpacity={0.8}
      onPress={onPress}
      disabled={disabled || loading}
      style={[
        styles.base,
        isPrimary && styles.primary,
        isSecondary && styles.secondary,
        isDestructive && styles.destructive,
        isGhost && styles.ghost,
        disabled && styles.disabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={isPrimary ? '#FFFFFF' : Colors.light.ink} size="small" />
      ) : (
        <Text
          style={[
            styles.text,
            isPrimary && styles.textPrimary,
            isSecondary && styles.textSecondary,
            isDestructive && styles.textDestructive,
            isGhost && styles.textGhost,
            disabled && styles.textDisabled,
            textStyle,
          ]}
        >
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  base: {
    height: 48,
    minHeight: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    marginVertical: 6,
  },
  primary: {
    backgroundColor: Colors.light.primary,
  },
  secondary: {
    backgroundColor: Colors.light.surface,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
  },
  destructive: {
    backgroundColor: Colors.light.error,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  disabled: {
    backgroundColor: Colors.light.hairline,
    borderColor: Colors.light.hairline,
  },
  text: {
    fontSize: 16,
    fontWeight: '600',
  },
  textPrimary: {
    color: '#FFFFFF',
  },
  textSecondary: {
    color: Colors.light.ink,
  },
  textDestructive: {
    color: '#FFFFFF',
  },
  textGhost: {
    color: Colors.light.primary,
  },
  textDisabled: {
    color: Colors.light.secondaryText,
  },
});

import React from 'react';
import { TextInput, View, Text, StyleSheet, TextInputProps } from 'react-native';
import { Colors } from '../../constants/colors';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, style, ...rest }) => {
  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <TextInput
        placeholderTextColor={Colors.light.secondaryText}
        style={[styles.input, error ? styles.inputError : null, style]}
        {...rest}
      />
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 6,
  },
  label: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.light.secondaryText,
    marginBottom: 6,
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
    borderRadius: 10,
    backgroundColor: Colors.light.surface,
    paddingHorizontal: 14,
    fontSize: 15,
    color: Colors.light.ink,
  },
  inputError: {
    borderColor: Colors.light.error,
  },
  error: {
    fontSize: 12,
    color: Colors.light.error,
    marginTop: 4,
  },
});

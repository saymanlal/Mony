import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Colors } from '../../constants/colors';
import { Check, X } from 'lucide-react-native';

export type StepStatus = 'pending' | 'running' | 'passed' | 'failed';

interface VerificationStepProps {
  label: string;
  status: StepStatus;
  detail?: string;
}

export const VerificationStep: React.FC<VerificationStepProps> = ({
  label,
  status,
  detail,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.iconContainer}>
        {status === 'pending' && <View style={styles.pendingDot} />}
        {status === 'running' && (
          <ActivityIndicator size="small" color={Colors.light.primary} />
        )}
        {status === 'passed' && <Check size={18} color={Colors.light.primary} strokeWidth={2.5} />}
        {status === 'failed' && <X size={18} color={Colors.light.error} strokeWidth={2.5} />}
      </View>
      <View style={styles.textContainer}>
        <Text style={[styles.label, status === 'passed' && styles.labelPassed]}>
          {label}
        </Text>
        {detail && <Text style={styles.detail}>{detail}</Text>}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.hairline,
  },
  iconContainer: {
    width: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  pendingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.light.hairline,
  },
  textContainer: {
    flex: 1,
  },
  label: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.light.ink,
  },
  labelPassed: {
    color: Colors.light.primary,
  },
  detail: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    marginTop: 2,
  },
});

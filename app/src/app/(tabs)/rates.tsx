import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/colors';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { ArrowLeftRight } from 'lucide-react-native';
import { formatINR, formatMON } from '../../utils/format';

export default function RatesScreen() {
  const [inrAmount, setInrAmount] = useState('500');
  const [monAmount, setMonAmount] = useState('0.0588');
  const [inrPerMon, setInrPerMon] = useState(8500.0);

  const handleInrChange = (val: string) => {
    setInrAmount(val);
    const num = parseFloat(val);
    if (!isNaN(num) && inrPerMon > 0) {
      setMonAmount((num / inrPerMon).toFixed(4));
    }
  };

  const handleMonChange = (val: string) => {
    setMonAmount(val);
    const num = parseFloat(val);
    if (!isNaN(num)) {
      setInrAmount((num * inrPerMon).toFixed(2));
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Exchange Rates</Text>
        <Text style={styles.subtitle}>
          Real-time conversion across Monad testnet and Indian Rupee.
        </Text>

        <Card style={styles.converterCard}>
          <Text style={styles.sectionHeader}>Instant Converter</Text>

          <Input
            label="Indian Rupee (INR)"
            value={inrAmount}
            onChangeText={handleInrChange}
            keyboardType="numeric"
          />

          <View style={styles.swapDivider}>
            <ArrowLeftRight size={20} color={Colors.light.secondaryText} />
          </View>

          <Input
            label="Monad (MON)"
            value={monAmount}
            onChangeText={handleMonChange}
            keyboardType="numeric"
          />

          <View style={styles.rateDetailRow}>
            <Text style={styles.rateDetailText}>Exchange Rate</Text>
            <Text style={styles.rateDetailValue}>
              1 MON = ₹{inrPerMon.toLocaleString('en-IN')}
            </Text>
          </View>
        </Card>

        <Text style={[styles.sectionHeader, { marginTop: 24, marginBottom: 12 }]}>
          Supported Denominations
        </Text>

        {[500, 200, 100, 50, 20, 10].map((denom) => {
          const monVal = (denom / inrPerMon).toFixed(4);
          return (
            <Card key={denom} style={styles.rateRowCard}>
              <View style={styles.rateRow}>
                <View>
                  <Text style={styles.denomTitle}>₹{denom} Banknote</Text>
                  <Text style={styles.denomSub}>Reserve Bank of India</Text>
                </View>
                <Text style={styles.denomMon}>{monVal} MON</Text>
              </View>
            </Card>
          );
        })}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.light.paper,
  },
  container: {
    padding: 20,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: Colors.light.ink,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.light.secondaryText,
    marginBottom: 20,
  },
  converterCard: {
    padding: 16,
  },
  sectionHeader: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.ink,
    marginBottom: 12,
  },
  swapDivider: {
    alignItems: 'center',
    marginVertical: 4,
  },
  rateDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.light.hairline,
  },
  rateDetailText: {
    fontSize: 13,
    color: Colors.light.secondaryText,
  },
  rateDetailValue: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.light.primary,
  },
  rateRowCard: {
    padding: 14,
    marginVertical: 4,
  },
  rateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  denomTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.light.ink,
  },
  denomSub: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    marginTop: 2,
  },
  denomMon: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.light.primary,
    fontVariant: ['tabular-nums'],
  },
});

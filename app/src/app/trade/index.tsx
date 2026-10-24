import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/colors';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useWalletStore } from '../../store/wallet';
import { api } from '../../services/api';
import { X, ArrowDown, ArrowUpDown } from 'lucide-react-native';

const TOKENS = [
  { symbol: 'MON', name: 'Monad', address: '0x0000000000000000000000000000000000000000', decimals: 18 },
  { symbol: 'mUSDC', name: 'Mock USD Coin', address: '0x1000000000000000000000000000000000000001', decimals: 6 },
  { symbol: 'mDAI', name: 'Mock Dai', address: '0x1000000000000000000000000000000000000002', decimals: 18 },
  { symbol: 'mWETH', name: 'Mock Wrapped Ether', address: '0x1000000000000000000000000000000000000003', decimals: 18 },
  { symbol: 'mWBTC', name: 'Mock Wrapped Bitcoin', address: '0x1000000000000000000000000000000000000004', decimals: 8 },
];

export default function TradeScreen() {
  const router = useRouter();
  const { address } = useWalletStore();

  const [tokenIn, setTokenIn] = useState(TOKENS[0]);
  const [tokenOut, setTokenOut] = useState(TOKENS[1]);
  const [amountIn, setAmountIn] = useState('1.0');
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleGetQuote = async () => {
    if (!address) return;
    try {
      setLoading(true);
      const res = await api.getExchangeQuote({
        user_address: address,
        token_in: tokenIn.address,
        token_out: tokenOut.address,
        amount_in: (parseFloat(amountIn) * 10 ** tokenIn.decimals).toFixed(0),
      });
      setQuote(res);
    } catch (e: any) {
      Alert.alert('Quote Error', e.message || 'Could not fetch quote');
    } finally {
      setLoading(false);
    }
  };

  const handleSwap = () => {
    Alert.alert('Swap Executed', 'Successfully swapped on MonyExchange contract.', [
      { text: 'Done', onPress: () => router.back() },
    ]);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Exchange</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeBtn}>
          <X size={20} color={Colors.light.ink} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        <Card style={styles.swapCard}>
          <View style={styles.tokenBox}>
            <View style={styles.tokenHeader}>
              <Text style={styles.boxLabel}>You Pay</Text>
              <Text style={styles.tokenSelectorText}>{tokenIn.symbol}</Text>
            </View>
            <Input
              value={amountIn}
              onChangeText={setAmountIn}
              keyboardType="numeric"
              placeholder="0.0"
              style={styles.amountInput}
            />
          </View>

          <View style={styles.switchIconRow}>
            <View style={styles.switchCircle}>
              <ArrowDown size={18} color={Colors.light.ink} />
            </View>
          </View>

          <View style={styles.tokenBox}>
            <View style={styles.tokenHeader}>
              <Text style={styles.boxLabel}>You Receive (Estimated)</Text>
              <Text style={styles.tokenSelectorText}>{tokenOut.symbol}</Text>
            </View>
            <Text style={styles.receiveText}>
              {quote ? (parseFloat(quote.amount_out) / 10 ** tokenOut.decimals).toFixed(4) : '100.0000'}
            </Text>
          </View>
        </Card>

        <Button
          title={quote ? "Confirm Swap" : "Get Signed Quote"}
          onPress={quote ? handleSwap : handleGetQuote}
          loading={loading}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.light.paper,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.hairline,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.light.ink,
  },
  closeBtn: {
    padding: 6,
  },
  container: {
    padding: 20,
  },
  swapCard: {
    padding: 16,
    marginBottom: 20,
  },
  tokenBox: {
    backgroundColor: Colors.light.paper,
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
  },
  tokenHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  boxLabel: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    textTransform: 'uppercase',
  },
  tokenSelectorText: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.light.primary,
  },
  amountInput: {
    fontSize: 20,
    fontWeight: '700',
    borderWidth: 0,
    backgroundColor: 'transparent',
    paddingHorizontal: 0,
    height: 36,
  },
  switchIconRow: {
    alignItems: 'center',
    marginVertical: -8,
    zIndex: 10,
  },
  switchCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.light.surface,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
    alignItems: 'center',
    justifyContent: 'center',
  },
  receiveText: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.light.ink,
    fontVariant: ['tabular-nums'],
    marginTop: 4,
  },
});

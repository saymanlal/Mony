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
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { parseEIP681 } from '../../utils/eip681';
import { useWalletStore } from '../../store/wallet';
import { X, QrCode } from 'lucide-react-native';

export default function SendScreen() {
  const router = useRouter();
  const { monBalance } = useWalletStore();

  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    const parsed = parseEIP681(recipient);
    const target = parsed?.targetAddress || recipient.trim();

    if (!target.startsWith('0x') || target.length !== 42) {
      Alert.alert('Invalid Address', 'Please provide a valid 42-character EVM address.');
      return;
    }

    const amtNum = parseFloat(amount);
    if (isNaN(amtNum) || amtNum <= 0) {
      Alert.alert('Invalid Amount', 'Please provide an amount greater than 0.');
      return;
    }

    setLoading(true);
    // Simulate transaction submission to Monad testnet
    setTimeout(() => {
      setLoading(false);
      Alert.alert(
        'Transfer Submitted',
        `Successfully sent ${amount} MON to ${target.substring(0, 8)}...`,
        [{ text: 'OK', onPress: () => router.back() }]
      );
    }, 1500);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Send MON</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeBtn}>
          <X size={20} color={Colors.light.ink} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        <Card style={styles.balanceInfoCard}>
          <Text style={styles.balanceInfoLabel}>Available to Send</Text>
          <Text style={styles.balanceInfoValue}>{monBalance} MON</Text>
        </Card>

        <Input
          label="Recipient Address or EIP-681 URI"
          placeholder="0x..."
          value={recipient}
          onChangeText={setRecipient}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <Input
          label="Amount (MON)"
          placeholder="0.00"
          value={amount}
          onChangeText={setAmount}
          keyboardType="numeric"
        />

        <View style={styles.feeCard}>
          <Text style={styles.feeLabel}>Network Fee (Monad Testnet)</Text>
          <Text style={styles.feeValue}>~0.00005 MON</Text>
        </View>

        <Button
          title="Review and Send"
          onPress={handleSend}
          loading={loading}
          disabled={!recipient.trim() || !amount.trim()}
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
  balanceInfoCard: {
    padding: 14,
    marginBottom: 16,
  },
  balanceInfoLabel: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    textTransform: 'uppercase',
  },
  balanceInfoValue: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.light.ink,
    marginTop: 4,
  },
  feeCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    marginTop: 4,
    marginBottom: 16,
  },
  feeLabel: {
    fontSize: 13,
    color: Colors.light.secondaryText,
  },
  feeValue: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.light.ink,
    fontFamily: 'monospace',
  },
});

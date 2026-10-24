import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Share,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/colors';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { truncateAddress } from '../../utils/format';
import { X, Share2, FileText, CheckCircle } from 'lucide-react-native';

export default function InvoiceScreen() {
  const router = useRouter();
  const { invoiceId } = useLocalSearchParams();

  const handleShare = async () => {
    await Share.share({
      message: `MONY Payment Receipt\nInvoice: INV-2026-${invoiceId}\nAmount: 0.0588 MON (₹500.00)\nExplorer: https://testnet.monadexplorer.com/tx/0x3a1f9e8d4c2b`,
      title: `Invoice_INV_${invoiceId}.pdf`,
    });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Invoice Receipt</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeBtn}>
          <X size={20} color={Colors.light.ink} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        <Card style={styles.invoiceCard}>
          <View style={styles.invoiceHeader}>
            <Text style={styles.brand}>MONY</Text>
            <Text style={styles.invoiceNumber}>INV-2026-{invoiceId || '8492'}</Text>
          </View>

          <View style={styles.statusRow}>
            <CheckCircle size={16} color={Colors.light.primary} />
            <Text style={styles.statusText}>Settled on Monad Testnet</Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.infoRow}>
            <Text style={styles.label}>Transaction Type</Text>
            <Text style={styles.value}>Physical Banknote Deposit</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.label}>Fiat Value</Text>
            <Text style={styles.value}>₹500.00 INR</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.label}>Exchange Rate</Text>
            <Text style={styles.value}>₹8,500.00 / MON</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.label}>Settled MON</Text>
            <Text style={[styles.value, styles.monValue]}>0.0588 MON</Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.infoRow}>
            <Text style={styles.label}>Transaction Hash</Text>
            <Text style={[styles.value, styles.mono]}>
              {truncateAddress('0x3a1f9e8d4c2b87a912e4f50689cb1289', 10, 8)}
            </Text>
          </View>
        </Card>

        <Button
          title="Share Receipt (Telegram / PDF)"
          onPress={handleShare}
          style={{ marginTop: 16 }}
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
  invoiceCard: {
    padding: 20,
  },
  invoiceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: 8,
  },
  brand: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.light.primary,
  },
  invoiceNumber: {
    fontSize: 13,
    color: Colors.light.secondaryText,
    fontFamily: 'monospace',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  statusText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.light.primary,
    marginLeft: 6,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.light.hairline,
    marginVertical: 14,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  label: {
    fontSize: 13,
    color: Colors.light.secondaryText,
  },
  value: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.light.ink,
  },
  monValue: {
    color: Colors.light.primary,
    fontSize: 15,
  },
  mono: {
    fontFamily: 'monospace',
  },
});

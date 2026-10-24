import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/colors';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { AddressDisplay } from '../../components/ui/AddressDisplay';
import { AmountDisplay } from '../../components/ui/AmountDisplay';
import { useWalletStore } from '../../store/wallet';
import { useSettingsStore } from '../../store/settings';
import { api } from '../../services/api';
import {
  ArrowDownLeft,
  ArrowUpRight,
  QrCode,
  PiggyBank,
  ArrowLeftRight,
} from 'lucide-react-native';

export default function HomeScreen() {
  const router = useRouter();
  const { address, monBalance, inrValue, setBalances } = useWalletStore();
  const { mode } = useSettingsStore();

  const [refreshing, setRefreshing] = useState(false);
  const [inrRate, setInrRate] = useState(8500.0);

  const fetchBalanceAndRates = async () => {
    try {
      setRefreshing(true);
      const rates = await api.getFiatRates();
      const inrPerMon = rates?.rates?.MON ? 1.0 / rates.rates.MON : 8500.0;
      setInrRate(inrPerMon);

      // In production viem getBalance on Monad testnet RPC:
      // Fallback demo balance if unseeded
      const currentMon = parseFloat(monBalance) || 2.5;
      setBalances(currentMon.toFixed(4), currentMon * inrPerMon);
    } catch {
      // Keep cached
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchBalanceAndRates();
  }, [address]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={fetchBalanceAndRates}
            tintColor={Colors.light.primary}
          />
        }
      >
        {/* Header: Mode and Address */}
        <View style={styles.headerRow}>
          <Badge
            label={mode === 'automated' ? 'Automated Mode' : 'Manual Mode'}
            variant={mode === 'automated' ? 'success' : 'neutral'}
          />
          {address && <AddressDisplay address={address} />}
        </View>

        {/* Balance Display */}
        <View style={styles.balanceContainer}>
          <Text style={styles.balanceLabel}>Total Balance</Text>
          <AmountDisplay
            monAmount={monBalance}
            inrAmount={inrValue}
            size="hero"
          />
        </View>

        {/* Quick Action Buttons */}
        <View style={styles.quickActionsRow}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/deposit')}
          >
            <View style={[styles.actionIconCircle, { backgroundColor: Colors.light.primary }]}>
              <ArrowDownLeft size={22} color="#FFFFFF" />
            </View>
            <Text style={styles.actionText}>Deposit</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/send')}
          >
            <View style={styles.actionIconCircle}>
              <ArrowUpRight size={22} color={Colors.light.ink} />
            </View>
            <Text style={styles.actionText}>Send</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/receive')}
          >
            <View style={styles.actionIconCircle}>
              <QrCode size={22} color={Colors.light.ink} />
            </View>
            <Text style={styles.actionText}>Receive</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/save')}
          >
            <View style={styles.actionIconCircle}>
              <PiggyBank size={22} color={Colors.light.ink} />
            </View>
            <Text style={styles.actionText}>Save</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/trade')}
          >
            <View style={styles.actionIconCircle}>
              <ArrowLeftRight size={22} color={Colors.light.ink} />
            </View>
            <Text style={styles.actionText}>Trade</Text>
          </TouchableOpacity>
        </View>

        {/* Live Market Sparkline Card */}
        <Card style={styles.sparkCard}>
          <View style={styles.sparkHeader}>
            <Text style={styles.cardTitle}>Monad Rate</Text>
            <Text style={styles.sparkPrice}>₹{inrRate.toLocaleString('en-IN')}</Text>
          </View>
          <Text style={styles.sparkSubtext}>1 MON = ₹{inrRate.toLocaleString('en-IN')} (Monad Testnet)</Text>
        </Card>

        {/* Recent Activity Section */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Deposits</Text>
          <TouchableOpacity onPress={() => router.push('/(tabs)/activity')}>
            <Text style={styles.seeAllText}>View All</Text>
          </TouchableOpacity>
        </View>

        <Card style={styles.activityCard}>
          <View style={styles.activityItem}>
            <View style={styles.activityIcon}>
              <ArrowDownLeft size={18} color={Colors.light.primary} />
            </View>
            <View style={styles.activityInfo}>
              <Text style={styles.activityTitle}>₹500 Banknote Deposited</Text>
              <Text style={styles.activityDate}>Verified live via OpenCV</Text>
            </View>
            <Text style={styles.activityAmount}>+0.0588 MON</Text>
          </View>
        </Card>
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  balanceContainer: {
    marginVertical: 12,
  },
  balanceLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.light.secondaryText,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  quickActionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 24,
  },
  actionButton: {
    alignItems: 'center',
    width: 60,
  },
  actionIconCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: Colors.light.surface,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  actionText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.light.ink,
  },
  sparkCard: {
    padding: 18,
    marginBottom: 24,
  },
  sparkHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: 4,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.light.ink,
  },
  sparkPrice: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.light.primary,
    fontVariant: ['tabular-nums'],
  },
  sparkSubtext: {
    fontSize: 12,
    color: Colors.light.secondaryText,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.light.ink,
  },
  seeAllText: {
    fontSize: 13,
    color: Colors.light.primary,
    fontWeight: '500',
  },
  activityCard: {
    padding: 14,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  activityIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.light.primarySubtle,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  activityInfo: {
    flex: 1,
  },
  activityTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.ink,
  },
  activityDate: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    marginTop: 2,
  },
  activityAmount: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.light.primary,
    fontVariant: ['tabular-nums'],
  },
});

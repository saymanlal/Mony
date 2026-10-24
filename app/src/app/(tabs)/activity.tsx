import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Share,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { ArrowDownLeft, ArrowUpRight, FileText, Download } from 'lucide-react-native';

const DEMO_ACTIVITIES = [
  {
    id: 'tx-1',
    type: 'deposit',
    title: 'Banknote Deposit',
    amount: '+0.0588 MON',
    fiat: '₹500.00',
    date: 'Today, 2:30 PM',
    status: 'confirmed',
    hash: '0x3a1f9e8d4c2b',
  },
  {
    id: 'tx-2',
    type: 'send',
    title: 'Sent to 0x71C...4982',
    amount: '-0.0200 MON',
    fiat: '₹170.00',
    date: 'Yesterday, 6:15 PM',
    status: 'confirmed',
    hash: '0x889d2f01ac54',
  },
  {
    id: 'tx-3',
    type: 'deposit',
    title: 'Banknote Deposit',
    amount: '+0.0118 MON',
    fiat: '₹100.00',
    date: 'Oct 20, 11:00 AM',
    status: 'confirmed',
    hash: '0x55bc32890ef1',
  },
];

export default function ActivityScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState<'all' | 'deposit' | 'send'>('all');

  const filtered = DEMO_ACTIVITIES.filter((item) => {
    if (filter === 'all') return true;
    return item.type === filter;
  });

  const handleExportCSV = async () => {
    const csvContent = [
      'Type,Title,Amount,Fiat,Date,Status,Hash',
      ...DEMO_ACTIVITIES.map(
        (a) => `${a.type},"${a.title}",${a.amount},${a.fiat},"${a.date}",${a.status},${a.hash}`
      ),
    ].join('\n');

    await Share.share({
      message: csvContent,
      title: 'mony_transactions.csv',
    });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.title}>Activity</Text>
            <Text style={styles.subtitle}>Unified ledger of deposits and transfers.</Text>
          </View>
          <TouchableOpacity
            style={styles.exportBtn}
            onPress={handleExportCSV}
          >
            <Download size={18} color={Colors.light.ink} />
          </TouchableOpacity>
        </View>

        {/* Filter Pills */}
        <View style={styles.filterRow}>
          {(['all', 'deposit', 'send'] as const).map((f) => (
            <TouchableOpacity
              key={f}
              onPress={() => setFilter(f)}
              style={[
                styles.filterPill,
                filter === f && styles.filterPillActive,
              ]}
            >
              <Text
                style={[
                  styles.filterText,
                  filter === f && styles.filterTextActive,
                ]}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* List */}
        {filtered.map((item) => (
          <TouchableOpacity
            key={item.id}
            onPress={() => router.push(`/invoices/${item.id}`)}
          >
            <Card style={styles.itemCard}>
              <View style={styles.itemRow}>
                <View style={styles.iconContainer}>
                  {item.type === 'deposit' ? (
                    <ArrowDownLeft size={18} color={Colors.light.primary} />
                  ) : (
                    <ArrowUpRight size={18} color={Colors.light.ink} />
                  )}
                </View>
                <View style={styles.itemDetails}>
                  <Text style={styles.itemTitle}>{item.title}</Text>
                  <Text style={styles.itemDate}>{item.date}</Text>
                </View>
                <View style={styles.amountContainer}>
                  <Text
                    style={[
                      styles.amountText,
                      item.type === 'deposit' && styles.amountDeposit,
                    ]}
                  >
                    {item.amount}
                  </Text>
                  <Text style={styles.fiatSubtext}>{item.fiat}</Text>
                </View>
              </View>
            </Card>
          </TouchableOpacity>
        ))}
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
    alignItems: 'flex-start',
    marginBottom: 16,
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
  },
  exportBtn: {
    padding: 10,
    backgroundColor: Colors.light.surface,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
    borderRadius: 10,
  },
  filterRow: {
    flexDirection: 'row',
    marginBottom: 18,
  },
  filterPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.light.surface,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
    marginRight: 8,
  },
  filterPillActive: {
    backgroundColor: Colors.light.primary,
    borderColor: Colors.light.primary,
  },
  filterText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.light.secondaryText,
  },
  filterTextActive: {
    color: '#FFFFFF',
  },
  itemCard: {
    padding: 14,
    marginVertical: 4,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.light.paper,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  itemDetails: {
    flex: 1,
  },
  itemTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.light.ink,
  },
  itemDate: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    marginTop: 2,
  },
  amountContainer: {
    alignItems: 'flex-end',
  },
  amountText: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.light.ink,
    fontVariant: ['tabular-nums'],
  },
  amountDeposit: {
    color: Colors.light.primary,
  },
  fiatSubtext: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    marginTop: 2,
  },
});

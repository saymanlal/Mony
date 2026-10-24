import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Share,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/colors';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { AddressDisplay } from '../../components/ui/AddressDisplay';
import { useWalletStore } from '../../store/wallet';
import { X, Share2, QrCode } from 'lucide-react-native';

export default function ReceiveScreen() {
  const router = useRouter();
  const { address } = useWalletStore();

  const handleShare = async () => {
    if (!address) return;
    await Share.share({
      message: `ethereum:${address}@10143`,
      title: 'Monad Address',
    });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Receive MON</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeBtn}>
          <X size={20} color={Colors.light.ink} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Your Monad Address</Text>
        <Text style={styles.subtitle}>
          Share this QR code or address to receive MON on Monad testnet.
        </Text>

        <Card style={styles.qrCard}>
          <View style={styles.qrPlaceholder}>
            <QrCode size={180} color={Colors.light.ink} strokeWidth={1.5} />
          </View>
          <View style={styles.addressWrapper}>
            {address && <AddressDisplay address={address} />}
          </View>
        </Card>

        <Button
          title="Share Payment Link"
          onPress={handleShare}
          variant="secondary"
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
    padding: 24,
    alignItems: 'center',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.light.ink,
    marginBottom: 4,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: Colors.light.secondaryText,
    textAlign: 'center',
    marginBottom: 24,
    paddingHorizontal: 20,
  },
  qrCard: {
    width: '100%',
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
  },
  qrPlaceholder: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 16,
  },
  addressWrapper: {
    marginTop: 8,
  },
});

import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { WalletService } from '../../services/wallet';
import { useWalletStore } from '../../store/wallet';

export default function ImportWalletScreen() {
  const router = useRouter();
  const { setAddress, setHasBackedUpPhrase } = useWalletStore();
  const [mnemonicInput, setMnemonicInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleImport = async () => {
    const clean = mnemonicInput.trim();
    const words = clean.split(/\s+/);
    if (words.length !== 12 && words.length !== 24) {
      Alert.alert('Invalid Phrase', 'Recovery phrase must be exactly 12 or 24 words.');
      return;
    }

    try {
      setLoading(true);
      const address = await WalletService.importWallet(clean);
      setAddress(address);
      setHasBackedUpPhrase(true);
      router.replace('/(tabs)');
    } catch (e: any) {
      Alert.alert('Import Failed', e.message || 'Could not derive wallet from phrase.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Import Wallet</Text>
      <Text style={styles.subtitle}>
        Enter your 12-word or 24-word recovery phrase separated by single spaces.
      </Text>

      <Input
        multiline
        numberOfLines={4}
        placeholder="apple banana cherry dog elephant fox grape horse igloo jaguar kangaroo lemon"
        value={mnemonicInput}
        onChangeText={setMnemonicInput}
        style={styles.textArea}
        autoCapitalize="none"
        autoCorrect={false}
      />

      <Button
        title="Restore Wallet"
        onPress={handleImport}
        loading={loading}
        disabled={!mnemonicInput.trim()}
      />

      <Button
        title="Back"
        variant="ghost"
        onPress={() => router.back()}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    justifyContent: 'center',
    backgroundColor: Colors.light.paper,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: Colors.light.ink,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: Colors.light.secondaryText,
    lineHeight: 24,
    marginBottom: 20,
  },
  textArea: {
    height: 120,
    textAlignVertical: 'top',
    paddingTop: 12,
    fontFamily: 'monospace',
    marginBottom: 20,
  },
});

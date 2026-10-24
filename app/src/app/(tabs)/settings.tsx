import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/colors';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { useSettingsStore } from '../../store/settings';
import { WalletService } from '../../services/wallet';
import { Shield, Key, Globe, Database } from 'lucide-react-native';

export default function SettingsScreen() {
  const {
    mode,
    setMode,
    biometricEnabled,
    setBiometricEnabled,
  } = useSettingsStore();

  const [revealedPhrase, setRevealedPhrase] = useState<string | null>(null);

  const handleRevealPhrase = async () => {
    try {
      const phrase = await WalletService.getStoredMnemonic();
      if (!phrase) {
        Alert.alert('Error', 'No phrase found');
        return;
      }
      setRevealedPhrase(phrase);
    } catch (e: any) {
      Alert.alert('Authentication Required', 'Unlock device to reveal secret phrase.');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Settings</Text>
        <Text style={styles.subtitle}>Execution modes, security parameters, and wallet backup.</Text>

        {/* Operating Mode Section */}
        <Card style={styles.sectionCard}>
          <View style={styles.row}>
            <View style={{ flex: 1, paddingRight: 12 }}>
              <Text style={styles.settingLabel}>Execution Mode</Text>
              <Text style={styles.settingDescription}>
                Automated mode deposits funds via relayer immediately upon acceptance. Manual mode requires local EIP-712 biometric signature.
              </Text>
            </View>
            <TouchableOpacity
              onPress={() => setMode(mode === 'automated' ? 'manual' : 'automated')}
              style={styles.modeToggle}
            >
              <Badge
                label={mode === 'automated' ? 'Automated' : 'Manual'}
                variant={mode === 'automated' ? 'success' : 'neutral'}
              />
            </TouchableOpacity>
          </View>
        </Card>

        {/* Security Settings */}
        <Card style={styles.sectionCard}>
          <Text style={styles.sectionHeader}>Security</Text>

          <View style={[styles.row, styles.divider]}>
            <View style={{ flex: 1 }}>
              <Text style={styles.settingLabel}>Biometric Authentication</Text>
              <Text style={styles.settingDescription}>
                Require biometric unlock for signing and reveal operations.
              </Text>
            </View>
            <Switch
              value={biometricEnabled}
              onValueChange={setBiometricEnabled}
              trackColor={{ false: Colors.light.hairline, true: Colors.light.primary }}
            />
          </View>

          <TouchableOpacity
            style={[styles.row, styles.divider]}
            onPress={handleRevealPhrase}
          >
            <View style={{ flex: 1 }}>
              <Text style={styles.settingLabel}>Backup Phrase</Text>
              <Text style={styles.settingDescription}>
                Reveal secret 12-word mnemonic recovery phrase.
              </Text>
              {revealedPhrase && (
                <Text style={styles.revealedText}>{revealedPhrase}</Text>
              )}
            </View>
            <Key size={18} color={Colors.light.ink} />
          </TouchableOpacity>
        </Card>

        {/* Network Information */}
        <Card style={styles.sectionCard}>
          <Text style={styles.sectionHeader}>Network</Text>
          <View style={styles.infoRow}>
            <Text style={styles.infoKey}>Network</Text>
            <Text style={styles.infoValue}>Monad Testnet</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoKey}>Chain ID</Text>
            <Text style={styles.infoValue}>10143</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoKey}>Currency</Text>
            <Text style={styles.infoValue}>MON</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoKey}>RPC URL</Text>
            <Text style={styles.infoValue}>https://testnet-rpc.monad.xyz</Text>
          </View>
        </Card>

        {/* App Version */}
        <View style={styles.versionContainer}>
          <Text style={styles.versionText}>MONY v1.0.0 (Production Build)</Text>
          <Text style={styles.versionText}>Monad Testnet Layer-2 Verification</Text>
        </View>
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
  sectionCard: {
    padding: 16,
    marginVertical: 6,
  },
  sectionHeader: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.light.ink,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  divider: {
    borderTopWidth: 1,
    borderTopColor: Colors.light.hairline,
    marginTop: 10,
    paddingTop: 12,
  },
  settingLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.light.ink,
  },
  settingDescription: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    marginTop: 2,
    lineHeight: 16,
  },
  modeToggle: {
    paddingVertical: 4,
  },
  revealedText: {
    marginTop: 8,
    fontFamily: 'monospace',
    fontSize: 13,
    color: Colors.light.primary,
    backgroundColor: Colors.light.paper,
    padding: 8,
    borderRadius: 6,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  infoKey: {
    fontSize: 13,
    color: Colors.light.secondaryText,
  },
  infoValue: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.light.ink,
    fontFamily: 'monospace',
  },
  versionContainer: {
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 12,
  },
  versionText: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    lineHeight: 18,
  },
});

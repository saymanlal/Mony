import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { WalletService } from '../../services/wallet';
import { useWalletStore } from '../../store/wallet';

export default function OnboardingScreen() {
  const router = useRouter();
  const { setAddress, setHasBackedUpPhrase } = useWalletStore();

  const [step, setStep] = useState<'welcome' | 'phrase' | 'quiz'>('welcome');
  const [mnemonicWords, setMnemonicWords] = useState<string[]>([]);
  const [walletAddress, setWalletAddress] = useState<string>('');
  const [quizIndices, setQuizIndices] = useState<number[]>([]);
  const [selectedWord, setSelectedWord] = useState<{ [index: number]: string }>({});

  const handleCreateWallet = async () => {
    try {
      const { mnemonic, address } = await WalletService.createWallet();
      const words = mnemonic.split(' ');
      setMnemonicWords(words);
      setWalletAddress(address);

      // Select 3 random indices to quiz
      const shuffled = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].sort(() => 0.5 - Math.random());
      setQuizIndices(shuffled.slice(0, 3).sort((a, b) => a - b));
      setStep('phrase');
    } catch (e: any) {
      Alert.alert('Wallet Error', e.message || 'Failed to create wallet');
    }
  };

  const handleCompleteQuiz = () => {
    for (const idx of quizIndices) {
      if (selectedWord[idx]?.trim().toLowerCase() !== mnemonicWords[idx]?.toLowerCase()) {
        Alert.alert('Verification Failed', `Word #${idx + 1} does not match your backup phrase.`);
        return;
      }
    }

    setAddress(walletAddress);
    setHasBackedUpPhrase(true);
    router.replace('/(tabs)');
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {step === 'welcome' && (
        <View style={styles.content}>
          <Text style={styles.brandTitle}>MONY</Text>
          <Text style={styles.subtitle}>
            Direct physical banknote verification to on-chain MON on Monad testnet.
          </Text>

          <Card style={styles.featureCard}>
            <Text style={styles.featureTitle}>Embedded Security</Text>
            <Text style={styles.featureText}>
              Your keys never leave this device. Encrypted locally with device credentials.
            </Text>
          </Card>

          <View style={styles.buttonGroup}>
            <Button title="Create New Wallet" onPress={handleCreateWallet} />
            <Button
              title="Import Existing Wallet"
              variant="secondary"
              onPress={() => router.push('/(auth)/import')}
            />
          </View>
        </View>
      )}

      {step === 'phrase' && (
        <View style={styles.content}>
          <Text style={styles.title}>Secret Recovery Phrase</Text>
          <Text style={styles.subtitle}>
            Write down these 12 words in exact order. Store them in a secure physical location.
          </Text>

          <View style={styles.wordsGrid}>
            {mnemonicWords.map((word, index) => (
              <View key={index} style={styles.wordItem}>
                <Text style={styles.wordIndex}>{index + 1}.</Text>
                <Text style={styles.wordText}>{word}</Text>
              </View>
            ))}
          </View>

          <Button title="Continue to Verification Quiz" onPress={() => setStep('quiz')} />
        </View>
      )}

      {step === 'quiz' && (
        <View style={styles.content}>
          <Text style={styles.title}>Verify Backup Phrase</Text>
          <Text style={styles.subtitle}>
            Confirm you have recorded your phrase by verifying the requested words.
          </Text>

          {quizIndices.map((wordIdx) => (
            <Card key={wordIdx} style={styles.quizCard}>
              <Text style={styles.quizLabel}>Word #{wordIdx + 1}</Text>
              <View style={styles.optionsRow}>
                {/* 3 candidate options: the correct word plus two distractors */}
                {[
                  mnemonicWords[wordIdx],
                  mnemonicWords[(wordIdx + 3) % 12],
                  mnemonicWords[(wordIdx + 7) % 12],
                ]
                  .sort()
                  .map((candidate, i) => (
                    <Button
                      key={i}
                      title={candidate}
                      variant={selectedWord[wordIdx] === candidate ? 'primary' : 'secondary'}
                      style={styles.quizOption}
                      onPress={() =>
                        setSelectedWord((prev) => ({ ...prev, [wordIdx]: candidate }))
                      }
                    />
                  ))}
              </View>
            </Card>
          ))}

          <Button
            title="Complete Setup"
            disabled={Object.keys(selectedWord).length < 3}
            onPress={handleCompleteQuiz}
          />
        </View>
      )}
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
  content: {
    flex: 1,
    justifyContent: 'center',
  },
  brandTitle: {
    fontSize: 48,
    fontWeight: '700',
    color: Colors.light.primary,
    letterSpacing: -1,
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
    marginBottom: 24,
  },
  featureCard: {
    marginVertical: 16,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.ink,
    marginBottom: 4,
  },
  featureText: {
    fontSize: 14,
    color: Colors.light.secondaryText,
    lineHeight: 20,
  },
  buttonGroup: {
    marginTop: 20,
  },
  wordsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginVertical: 16,
  },
  wordItem: {
    width: '48%',
    flexDirection: 'row',
    backgroundColor: Colors.light.surface,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
    borderRadius: 8,
    padding: 12,
    marginVertical: 6,
  },
  wordIndex: {
    fontSize: 14,
    color: Colors.light.secondaryText,
    width: 28,
  },
  wordText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.light.ink,
    fontFamily: 'monospace',
  },
  quizCard: {
    marginBottom: 14,
  },
  quizLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.light.ink,
    marginBottom: 10,
  },
  optionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  quizOption: {
    flex: 1,
    marginHorizontal: 4,
    height: 42,
  },
});

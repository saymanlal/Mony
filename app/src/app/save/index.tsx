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
import { X, PiggyBank, Lock, ArrowUpRight } from 'lucide-react-native';

const DEMO_GOALS = [
  {
    id: 'goal-1',
    name: 'Monad Validator Reserve',
    target: 10.0,
    current: 4.5,
    lockDays: 180,
    accruedYield: 0.125,
    apr: '15.0%',
  },
  {
    id: 'goal-2',
    name: 'Emergency Buffer',
    target: 5.0,
    current: 5.0,
    lockDays: 30,
    accruedYield: 0.045,
    apr: '8.0%',
  },
];

export default function SaveScreen() {
  const router = useRouter();
  const [goals, setGoals] = useState(DEMO_GOALS);
  const [showNewGoal, setShowNewGoal] = useState(false);
  const [goalName, setGoalName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');

  const handleCreateGoal = () => {
    if (!goalName || !targetAmount) {
      Alert.alert('Required Fields', 'Please enter a goal name and target amount.');
      return;
    }
    const newG = {
      id: `goal-${Date.now()}`,
      name: goalName,
      target: parseFloat(targetAmount),
      current: 0.0,
      lockDays: 90,
      accruedYield: 0.0,
      apr: '10.0%',
    };
    setGoals([newG, ...goals]);
    setShowNewGoal(false);
    setGoalName('');
    setTargetAmount('');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Savings Vault</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeBtn}>
          <X size={20} color={Colors.light.ink} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        <Card style={styles.bannerCard}>
          <Text style={styles.bannerTitle}>Earn Up to 15% Testnet APR</Text>
          <Text style={styles.bannerText}>
            Accrues per second from the rewards pool funded by contract owner.
          </Text>
        </Card>

        {!showNewGoal ? (
          <Button
            title="Create New Goal"
            onPress={() => setShowNewGoal(true)}
            style={{ marginBottom: 20 }}
          />
        ) : (
          <Card style={styles.newGoalCard}>
            <Text style={styles.newGoalTitle}>New Savings Target</Text>
            <Input
              label="Goal Name"
              placeholder="e.g. College Fund"
              value={goalName}
              onChangeText={setGoalName}
            />
            <Input
              label="Target Amount (MON)"
              placeholder="10.0"
              value={targetAmount}
              onChangeText={setTargetAmount}
              keyboardType="numeric"
            />
            <Button title="Confirm Goal" onPress={handleCreateGoal} />
            <Button
              title="Cancel"
              variant="ghost"
              onPress={() => setShowNewGoal(false)}
            />
          </Card>
        )}

        <Text style={styles.sectionTitle}>Active Vault Goals</Text>

        {goals.map((g) => {
          const progress = Math.min(100, Math.round((g.current / g.target) * 100));
          return (
            <Card key={g.id} style={styles.goalCard}>
              <View style={styles.goalHeader}>
                <View>
                  <Text style={styles.goalName}>{g.name}</Text>
                  <Text style={styles.goalLock}>{g.lockDays} Days Lock ({g.apr} APR)</Text>
                </View>
                <View style={styles.yieldBadge}>
                  <Text style={styles.yieldText}>+{g.accruedYield} MON</Text>
                </View>
              </View>

              <View style={styles.progressTrack}>
                <View style={[styles.progressFill, { width: `${progress}%` }]} />
              </View>

              <View style={styles.goalFooter}>
                <Text style={styles.progressLabel}>
                  {g.current.toFixed(2)} / {g.target.toFixed(2)} MON ({progress}%)
                </Text>
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
  bannerCard: {
    backgroundColor: Colors.light.primarySubtle,
    borderWidth: 0,
    padding: 16,
    marginBottom: 16,
  },
  bannerTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.light.primary,
    marginBottom: 4,
  },
  bannerText: {
    fontSize: 13,
    color: Colors.light.ink,
    lineHeight: 18,
  },
  newGoalCard: {
    padding: 16,
    marginBottom: 20,
  },
  newGoalTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.ink,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.light.ink,
    marginBottom: 12,
  },
  goalCard: {
    padding: 16,
    marginVertical: 6,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  goalName: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.ink,
  },
  goalLock: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    marginTop: 2,
  },
  yieldBadge: {
    backgroundColor: Colors.light.primarySubtle,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  yieldText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.light.primary,
  },
  progressTrack: {
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.light.hairline,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: Colors.light.primary,
  },
  goalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressLabel: {
    fontSize: 12,
    color: Colors.light.secondaryText,
    fontVariant: ['tabular-nums'],
  },
});

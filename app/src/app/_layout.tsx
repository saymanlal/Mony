import React, { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator } from 'react-native';
import { Colors } from '../constants/colors';
import { WalletService } from '../services/wallet';
import { useWalletStore } from '../store/wallet';

export default function RootLayout() {
  const router = useRouter();
  const segments = useSegments();
  const [loading, setLoading] = useState(true);
  const { address, setAddress } = useWalletStore();

  useEffect(() => {
    async function checkAuth() {
      try {
        const storedAddress = await WalletService.getActiveAddress();
        setAddress(storedAddress);
      } catch {
        setAddress(null);
      } finally {
        setLoading(false);
      }
    }
    checkAuth();
  }, []);

  useEffect(() => {
    if (loading) return;

    const inAuthGroup = segments[0] === '(auth)';

    if (!address && !inAuthGroup) {
      router.replace('/(auth)/onboarding');
    } else if (address && inAuthGroup) {
      router.replace('/(tabs)');
    }
  }, [address, loading, segments]);

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: Colors.light.paper, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={Colors.light.primary} />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: Colors.light.paper },
        }}
      >
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen
          name="deposit/index"
          options={{ presentation: 'fullScreenModal', headerShown: false }}
        />
        <Stack.Screen
          name="send/index"
          options={{ presentation: 'modal', headerShown: false }}
        />
        <Stack.Screen
          name="receive/index"
          options={{ presentation: 'modal', headerShown: false }}
        />
        <Stack.Screen
          name="save/index"
          options={{ presentation: 'card', headerShown: false }}
        />
        <Stack.Screen
          name="trade/index"
          options={{ presentation: 'card', headerShown: false }}
        />
        <Stack.Screen
          name="invoices/[invoiceId]"
          options={{ presentation: 'modal', headerShown: false }}
        />
        <Stack.Screen name="+not-found" options={{ title: 'Not Found' }} />
      </Stack>
    </>
  );
}

import { Stack } from 'expo-router';
import { Colors } from '../../constants/colors';

export default function AuthLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: Colors.light.paper },
      }}
    >
      <Stack.Screen name="onboarding" />
      <Stack.Screen name="import" />
    </Stack>
  );
}

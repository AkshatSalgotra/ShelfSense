import React from 'react';
import { Stack } from 'expo-router';

export default function CashierLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="pos" />
    </Stack>
  );
}

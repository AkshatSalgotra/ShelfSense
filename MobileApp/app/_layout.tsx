import { useEffect } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet, Text } from 'react-native';
import { useAuthStore } from '../stores/authStore';
import { colors } from '../constants/theme';
import Toast from 'react-native-toast-message';
import * as SecureStore from 'expo-secure-store';

import { useFonts, Syne_400Regular, Syne_600SemiBold, Syne_700Bold } from '@expo-google-fonts/syne';
import { DMSans_400Regular, DMSans_500Medium, DMSans_700Bold } from '@expo-google-fonts/dm-sans';
import { JetBrainsMono_400Regular } from '@expo-google-fonts/jetbrains-mono';

function AuthGate({ children }: { children: React.ReactNode }) {
  const { token, role, setAuth } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    // Basic auth restore logic
    const restoreAuth = async () => {
      try {
        const storedToken = await SecureStore.getItemAsync('token');
        if (storedToken && !token) {
          // If we had a token, ideally we'd decode it or verify with backend.
          // For now, if we have a token but no role in store, we might need them to login again 
          // or we can decode the JWT to get the role if we have a lib for it.
          // To keep it simple, we will let index.tsx handle the initial routing.
        }
      } catch (e) { }
    };
    restoreAuth();
  }, []);

  return <>{children}</>;
}

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    Syne_400Regular,
    Syne_600SemiBold,
    Syne_700Bold,
    DMSans_400Regular,
    DMSans_500Medium,
    DMSans_700Bold,
    JetBrainsMono_400Regular,
  });

  if (!fontsLoaded) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={{ color: 'white' }}>Loading Fonts...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <AuthGate>
        <Stack screenOptions={{ headerShown: false }} />
      </AuthGate>
      <Toast />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
});

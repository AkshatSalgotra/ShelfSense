import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Pressable, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';
import { jwtDecode } from 'jwt-decode';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuthStore } from '../stores/authStore';
import { colors, type, spacing, radius } from '../constants/theme';

export default function Index() {
  const router = useRouter();
  const { token, role, setAuth } = useAuthStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const storedToken = await SecureStore.getItemAsync('token');
        if (storedToken) {
          try {
            const decoded: any = jwtDecode(storedToken);
            // Assuming decoded token has 'role', 'shop_id', 'full_name'
            // If the token is valid, set auth and route
            const exp = decoded.exp * 1000;
            if (Date.now() >= exp) {
              await SecureStore.deleteItemAsync('token');
            } else {
              const decodedRole = decoded.role || 'owner'; // default to owner if not specified
              setAuth(storedToken, decodedRole, decoded.shop_id || '', decoded.full_name || '');
              if (decodedRole === 'owner') {
                router.replace('/(manager)/dashboard');
              } else if (decodedRole === 'cashier') {
                router.replace('/(cashier)/pos');
              }
              return;
            }
          } catch (e) {
            await SecureStore.deleteItemAsync('token');
          }
        }
      } catch (e) {
        console.error("Auth check error", e);
      } finally {
        setIsInitializing(false);
      }
    };
    
    // Only check if we don't already have it in state
    if (!token) {
      checkAuth();
    } else {
      setIsInitializing(false);
      if (role === 'owner') {
        router.replace('/(manager)/dashboard');
      } else if (role === 'cashier') {
        router.replace('/(cashier)/pos');
      }
    }
  }, [token, role]);

  if (isInitializing) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logoText}>ShelfSense</Text>
        <Text style={styles.subtitle}>Select your role to continue</Text>
      </View>

      <View style={styles.cardsContainer}>
        <Pressable 
          style={({ pressed }) => [styles.card, pressed && { opacity: 0.75 }]}
          onPress={() => router.push('/(auth)/manager-login')}
        >
          <Text style={styles.cardEmoji}>🏪</Text>
          <Text style={styles.cardTitle}>Manager</Text>
          <Text style={styles.cardDesc}>Manage inventory, staff & forecasts</Text>
        </Pressable>

        <Pressable 
          style={({ pressed }) => [styles.card, pressed && { opacity: 0.75 }]}
          onPress={() => router.push('/(auth)/cashier-login')}
        >
          <Text style={styles.cardEmoji}>🧾</Text>
          <Text style={styles.cardTitle}>Cashier</Text>
          <Text style={styles.cardDesc}>Process sales & payments</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
    padding: spacing.xl,
  },
  header: {
    marginTop: spacing.xxl * 2,
    marginBottom: spacing.xxl,
    alignItems: 'center',
  },
  logoText: {
    ...type.displayLg,
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  subtitle: {
    ...type.bodyLg,
    color: colors.textSecondary,
  },
  cardsContainer: {
    gap: spacing.lg,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    alignItems: 'center',
  },
  cardEmoji: {
    fontSize: 48,
    marginBottom: spacing.sm,
  },
  cardTitle: {
    ...type.headingMd,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  cardDesc: {
    ...type.bodySm,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});

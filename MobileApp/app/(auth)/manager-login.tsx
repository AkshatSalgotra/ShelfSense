import React, { useState } from 'react';
import {
  View, Text, TextInput, Pressable, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuthStore } from '../../stores/authStore';
import { colors, type, spacing, radius } from '../../constants/theme';
import api from '../../lib/api';
import * as SecureStore from 'expo-secure-store';
import { jwtDecode } from 'jwt-decode';

export default function ManagerLogin() {
  const router = useRouter();
  const setAuth = useAuthStore(state => state.setAuth);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('username', email.trim());
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const { access_token } = response.data;
      await SecureStore.setItemAsync('token', access_token);
      
      const decoded: any = jwtDecode(access_token);
      const decodedRole = decoded.role || 'owner';
      
      setAuth(
        access_token, 
        decodedRole, 
        decoded.shop_id || '', 
        decoded.full_name || 'Manager'
      );

      if (decodedRole === 'owner') {
        router.replace('/(manager)/dashboard');
      } else {
        setError('Only managers can log in here');
        await SecureStore.deleteItemAsync('token');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.backBtn}>
            <MaterialCommunityIcons name="arrow-left" size={24} color={colors.textPrimary} />
          </Pressable>
          <Text style={styles.logoText}>ShelfSense</Text>
          <Text style={styles.subtitle}>Manager Sign In</Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Email Address</Text>
            <TextInput
              style={styles.input}
              placeholder="ravi@kirana.com"
              placeholderTextColor={colors.textMuted}
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={styles.input}
              placeholder="••••••••"
              placeholderTextColor={colors.textMuted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
          </View>

          {error && <Text style={styles.errorText}>{error}</Text>}

          <Pressable
            style={({ pressed }) => [
              styles.signInBtn,
              pressed && { opacity: 0.8 },
              loading && { opacity: 0.6 }
            ]}
            onPress={handleLogin}
            disabled={loading}
          >
            <Text style={styles.signInBtnText}>
              {loading ? 'Signing In...' : 'Sign In'}
            </Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  scroll: {
    flexGrow: 1,
    padding: spacing.xl,
  },
  header: {
    marginTop: spacing.xxl,
    marginBottom: spacing.xxl,
  },
  backBtn: {
    marginBottom: spacing.lg,
  },
  logoText: {
    ...type.displaySm,
    color: colors.primary,
  },
  subtitle: {
    ...type.headingMd,
    color: colors.textPrimary,
    marginTop: spacing.xs,
  },
  form: {
    gap: spacing.lg,
  },
  inputGroup: {
    gap: spacing.sm,
  },
  label: {
    ...type.label,
    color: colors.textSecondary,
  },
  input: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    color: colors.textPrimary,
    ...type.bodyLg,
  },
  errorText: {
    ...type.bodySm,
    color: colors.danger,
    marginTop: -spacing.sm,
  },
  signInBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
    marginTop: spacing.md,
  },
  signInBtnText: {
    ...type.headingMd,
    color: colors.bg,
  },
});

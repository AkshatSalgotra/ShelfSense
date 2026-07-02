import React, { useState } from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TextInput, 
  Pressable, Alert, KeyboardAvoidingView, Platform 
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors, type, spacing, radius } from '../../../constants/theme';
import api from '../../../lib/api';

export default function AddCashier() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    email: '',
    password: '',
    confirm_password: '',
  });

  const handleSubmit = async () => {
    if (!form.full_name.trim() || !form.phone.trim() || !form.password.trim()) {
      Alert.alert("Error", "Please fill all required fields (*)");
      return;
    }

    if (form.password !== form.confirm_password) {
      Alert.alert("Error", "Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        full_name: form.full_name.trim(),
        phone: form.phone.trim(), // Correct field name for backend
        email: form.email.trim() || undefined,
        password: form.password,
      };

      await api.post('/staff/create', payload);
      Alert.alert("Success", "Cashier account created successfully", [
        { text: "OK", onPress: () => router.back() }
      ]);
    } catch (err: any) {
      console.error("Create staff error:", err.response?.data);
      const errorMsg = typeof err.response?.data?.detail === 'string' 
        ? err.response.data.detail 
        : Array.isArray(err.response?.data?.detail)
          ? err.response.data.detail.map((e: any) => e.msg).join(', ')
          : "Failed to create cashier";
      
      Alert.alert("Error", errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backBtn}>
          <MaterialCommunityIcons name="arrow-left" size={24} color={colors.textPrimary} />
        </Pressable>
        <Text style={styles.title}>Add New Cashier</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.form}>
          <InputGroup 
            label="Full Name *" 
            value={form.full_name} 
            onChange={(t) => setForm({...form, full_name: t})} 
            placeholder="e.g. Priya Sharma" 
          />
          
          <InputGroup 
            label="Phone Number * (Login Username)" 
            value={form.phone} 
            onChange={(t) => setForm({...form, phone: t})} 
            placeholder="e.g. 9876543210" 
            keyboardType="phone-pad"
          />

          <InputGroup 
            label="Email (Optional)" 
            value={form.email} 
            onChange={(t) => setForm({...form, email: t})} 
            placeholder="e.g. priya@example.com" 
            keyboardType="email-address"
          />

          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <InputGroup 
                label="Password *" 
                value={form.password} 
                onChange={(t) => setForm({...form, password: t})} 
                placeholder="••••••••" 
                secureTextEntry
              />
            </View>
            <View style={{ flex: 1 }}>
              <InputGroup 
                label="Confirm Password *" 
                value={form.confirm_password} 
                onChange={(t) => setForm({...form, confirm_password: t})} 
                placeholder="••••••••" 
                secureTextEntry
              />
            </View>
          </View>

          <Pressable 
            style={[styles.submitBtn, loading && { opacity: 0.6 }]}
            onPress={handleSubmit}
            disabled={loading}
          >
            <Text style={styles.submitBtnText}>
              {loading ? 'Creating Account...' : 'Create Cashier Account'}
            </Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function InputGroup({ label, value, onChange, placeholder, keyboardType = 'default', secureTextEntry = false }: any) {
  return (
    <View style={styles.inputGroup}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor={colors.textMuted}
        keyboardType={keyboardType}
        secureTextEntry={secureTextEntry}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  header: {
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    ...type.displaySm,
    color: colors.textPrimary,
  },
  scroll: {
    padding: spacing.lg,
    paddingBottom: 50,
  },
  form: {
    gap: spacing.lg,
  },
  inputGroup: {
    gap: spacing.xs,
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
  row: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  submitBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.lg,
    alignItems: 'center',
    marginTop: spacing.xl,
  },
  submitBtnText: {
    ...type.headingMd,
    color: colors.bg,
  },
});

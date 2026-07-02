import React, { useState } from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TextInput, 
  Pressable, Alert, KeyboardAvoidingView, Platform 
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors, type, spacing, radius } from '../../../constants/theme';
import api from '../../../lib/api';

const UNITS = ['pcs', 'kg', 'g', 'L', 'ml', 'units'];

export default function AddProduct() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    product_name: '',
    category: '',
    sku_code: '',
    unit: 'pcs',
    cost_price: '',
    selling_price: '',
    current_stock: '',
    reorder_threshold: '',
  });

  const handleSubmit = async () => {
    if (!form.product_name.trim()) {
      Alert.alert("Error", "Product Name is required");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...form,
        cost_price: parseFloat(form.cost_price) || 0,
        selling_price: parseFloat(form.selling_price) || 0,
        current_stock: parseInt(form.current_stock) || 0,
        reorder_threshold: parseInt(form.reorder_threshold) || 10,
      };

      await api.post('/inventory/', payload);
      Alert.alert("Success", "Product added successfully", [
        { text: "OK", onPress: () => router.back() }
      ]);
    } catch (err) {
      Alert.alert("Error", "Failed to add product");
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
        <Text style={styles.title}>Add New Product</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.form}>
          <InputGroup label="Product Name *" value={form.product_name} onChange={(t) => setForm({...form, product_name: t})} placeholder="e.g. Parle-G Biscuits 800g" />
          
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <InputGroup label="Category" value={form.category} onChange={(t) => setForm({...form, category: t})} placeholder="e.g. Snacks" />
            </View>
            <View style={{ flex: 1 }}>
              <InputGroup label="SKU Code" value={form.sku_code} onChange={(t) => setForm({...form, sku_code: t})} placeholder="e.g. PAR001" />
            </View>
          </View>

          <View style={styles.sectionLabelRow}>
            <Text style={styles.sectionLabel}>Unit Type</Text>
          </View>
          <View style={styles.unitRow}>
            {UNITS.map(u => (
              <Pressable 
                key={u} 
                style={[styles.unitChip, form.unit === u && styles.unitChipActive]}
                onPress={() => setForm({...form, unit: u})}
              >
                <Text style={[styles.unitText, form.unit === u && styles.unitTextActive]}>{u}</Text>
              </Pressable>
            ))}
          </View>

          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <InputGroup label="Cost Price" value={form.cost_price} onChange={(t) => setForm({...form, cost_price: t})} placeholder="₹0" keyboardType="numeric" />
            </View>
            <View style={{ flex: 1 }}>
              <InputGroup label="Selling Price" value={form.selling_price} onChange={(t) => setForm({...form, selling_price: t})} placeholder="₹0" keyboardType="numeric" />
            </View>
          </View>

          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <InputGroup label="Current Stock" value={form.current_stock} onChange={(t) => setForm({...form, current_stock: t})} placeholder="0" keyboardType="numeric" />
            </View>
            <View style={{ flex: 1 }}>
              <InputGroup label="Reorder Threshold" value={form.reorder_threshold} onChange={(t) => setForm({...form, reorder_threshold: t})} placeholder="10" keyboardType="numeric" />
            </View>
          </View>

          <Pressable 
            style={[styles.submitBtn, loading && { opacity: 0.6 }]}
            onPress={handleSubmit}
            disabled={loading}
          >
            <Text style={styles.submitBtnText}>
              {loading ? 'Adding...' : 'Add Product'}
            </Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function InputGroup({ label, value, onChange, placeholder, keyboardType = 'default' }: any) {
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
  sectionLabelRow: {
    marginTop: spacing.sm,
  },
  sectionLabel: {
    ...type.label,
    color: colors.textSecondary,
  },
  unitRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  unitChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 8,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  unitChipActive: {
    backgroundColor: colors.primaryDim,
    borderColor: colors.primary,
  },
  unitText: {
    ...type.bodySm,
    color: colors.textSecondary,
  },
  unitTextActive: {
    color: colors.primary,
    fontWeight: 'bold',
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

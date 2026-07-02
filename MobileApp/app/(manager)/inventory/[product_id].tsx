import React, { useEffect, useState } from 'react';
import { 
  View, Text, StyleSheet, ScrollView, TextInput, 
  Pressable, ActivityIndicator, Alert 
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { BarChart } from 'react-native-gifted-charts';
import { colors, type, spacing, radius } from '../../../constants/theme';
import api from '../../../lib/api';

export default function ProductDetail() {
  const { product_id } = useLocalSearchParams();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('Details'); // Details | Forecast
  const [loading, setLoading] = useState(true);
  const [product, setProduct] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchProduct();
  }, [product_id]);

  const fetchProduct = async () => {
    try {
      const res = await api.get(`/inventory/${product_id}`);
      setProduct(res.data);
    } catch (err) {
      console.error("Fetch product error", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchForecast = async () => {
    try {
      const res = await api.get(`/predictions/${product_id}?days=30`);
      setForecast(res.data);
    } catch (err) {
      console.error("Fetch forecast error", err);
    }
  };

  useEffect(() => {
    if (activeTab === 'Forecast' && !forecast) {
      fetchForecast();
    }
  }, [activeTab]);

  const handleUpdate = async () => {
    setSaving(true);
    try {
      await api.patch(`/inventory/${product_id}`, product);
      setIsDirty(false);
      Alert.alert("Success", "Product updated successfully");
    } catch (err) {
      Alert.alert("Error", "Failed to update product");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      "Delete Product",
      "Are you sure you want to delete this product? This action cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Delete", 
          style: "destructive",
          onPress: async () => {
            try {
              await api.delete(`/inventory/${product_id}`);
              router.back();
            } catch (err) {
              Alert.alert("Error", "Failed to delete product");
            }
          }
        }
      ]
    );
  };

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center' }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!product) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={{ color: colors.textSecondary }}>Product not found</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backBtn}>
          <MaterialCommunityIcons name="arrow-left" size={24} color={colors.textPrimary} />
        </Pressable>
        <TextInput
          style={styles.productNameInput}
          value={product.product_name}
          onChangeText={(text) => {
            setProduct({ ...product, product_name: text });
            setIsDirty(true);
          }}
        />
      </View>

      <View style={styles.tabBar}>
        {['Details', 'Forecast'].map(tab => (
          <Pressable 
            key={tab} 
            onPress={() => setActiveTab(tab)}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>{tab}</Text>
          </Pressable>
        ))}
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {activeTab === 'Details' ? (
          <View style={styles.detailsTab}>
            <View style={styles.infoGrid}>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>Category</Text>
                <Text style={styles.infoValue}>{product.category || 'N/A'}</Text>
              </View>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>Unit</Text>
                <Text style={styles.infoValue}>{product.unit || 'pcs'}</Text>
              </View>
              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>SKU Code</Text>
                <Text style={styles.infoValue}>{product.sku_code || 'N/A'}</Text>
              </View>
            </View>

            <View style={styles.editableSection}>
              <Text style={styles.sectionLabel}>Current Stock</Text>
              <View style={styles.stockEditRow}>
                <TextInput
                  style={styles.stockInput}
                  value={product.current_stock.toString()}
                  keyboardType="numeric"
                  onChangeText={(text) => {
                    setProduct({ ...product, current_stock: parseInt(text) || 0 });
                    setIsDirty(true);
                  }}
                />
                <Text style={styles.unitText}>{product.unit || 'units'}</Text>
              </View>

              <View style={styles.priceRow}>
                <View style={styles.priceInputGroup}>
                  <Text style={styles.sectionLabel}>Cost Price</Text>
                  <TextInput
                    style={styles.priceInput}
                    value={product.cost_price?.toString()}
                    keyboardType="numeric"
                    placeholder="₹0"
                    placeholderTextColor={colors.textMuted}
                    onChangeText={(text) => {
                      setProduct({ ...product, cost_price: parseFloat(text) || 0 });
                      setIsDirty(true);
                    }}
                  />
                </View>
                <View style={styles.priceInputGroup}>
                  <Text style={styles.sectionLabel}>Selling Price</Text>
                  <TextInput
                    style={styles.priceInput}
                    value={product.selling_price.toString()}
                    keyboardType="numeric"
                    placeholder="₹0"
                    placeholderTextColor={colors.textMuted}
                    onChangeText={(text) => {
                      setProduct({ ...product, selling_price: parseFloat(text) || 0 });
                      setIsDirty(true);
                    }}
                  />
                </View>
              </View>

              <Text style={styles.sectionLabel}>Reorder Threshold</Text>
              <TextInput
                style={styles.priceInput}
                value={product.reorder_threshold.toString()}
                keyboardType="numeric"
                onChangeText={(text) => {
                  setProduct({ ...product, reorder_threshold: parseInt(text) || 0 });
                  setIsDirty(true);
                }}
              />
            </View>

            <Pressable 
              style={[styles.deleteBtn, { opacity: saving ? 0.6 : 1 }]}
              onPress={handleDelete}
            >
              <MaterialCommunityIcons name="trash-can-outline" size={20} color={colors.danger} />
              <Text style={styles.deleteBtnText}>Delete Product</Text>
            </Pressable>
          </View>
        ) : (
          <View style={styles.forecastTab}>
            {forecast ? (
              <>
                <View style={styles.chartCard}>
                  <Text style={styles.chartTitle}>30-Day Demand Forecast</Text>
                  <BarChart
                    data={forecast.daily_forecast.map((d: any) => ({ 
                      value: d.quantity, 
                      label: new Date(d.date).getDate().toString() 
                    }))}
                    barWidth={18}
                    noOfSections={4}
                    barBorderRadius={4}
                    frontColor={colors.primary}
                    yAxisThickness={0}
                    xAxisThickness={0}
                    yAxisTextStyle={{ color: colors.textSecondary }}
                    xAxisLabelTextStyle={{ color: colors.textSecondary }}
                    hideRules
                  />
                </View>

                <View style={styles.forecastMetrics}>
                  <MetricCard 
                    title="Predicted Demand" 
                    value={forecast.total_predicted_demand} 
                    unit={product.unit} 
                  />
                  <MetricCard 
                    title="Current Stock" 
                    value={product.current_stock} 
                    unit={product.unit} 
                  />
                  <MetricCard 
                    title="Recommended Order" 
                    value={forecast.recommended_qty} 
                    unit={product.unit} 
                    highlight 
                  />
                </View>

                <View style={styles.forecastBadges}>
                  <Badge label="Confidence: HIGH" color={colors.primary} />
                  <Badge label={`Model: ${forecast.model_tier}`} color={colors.info} />
                </View>
              </>
            ) : (
              <ActivityIndicator size="small" color={colors.primary} style={{ marginTop: 50 }} />
            )}
          </View>
        )}
      </ScrollView>

      {isDirty && (
        <View style={styles.saveFooter}>
          <Pressable 
            style={[styles.saveBtn, saving && { opacity: 0.6 }]}
            onPress={handleUpdate}
            disabled={saving}
          >
            <Text style={styles.saveBtnText}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

function MetricCard({ title, value, unit, highlight }: any) {
  return (
    <View style={[styles.metricCard, highlight && { borderColor: colors.primary }]}>
      <Text style={styles.metricTitle}>{title}</Text>
      <Text style={[styles.metricValue, highlight && { color: colors.primary }]}>
        {value} <Text style={styles.metricUnit}>{unit}</Text>
      </Text>
    </View>
  );
}

function Badge({ label, color }: any) {
  return (
    <View style={[styles.badge, { backgroundColor: color + '20' }]}>
      <Text style={[styles.badgeText, { color }]}>{label}</Text>
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
  productNameInput: {
    flex: 1,
    ...type.displaySm,
    color: colors.textPrimary,
    padding: 0,
  },
  tabBar: {
    flexDirection: 'row',
    paddingHorizontal: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  tab: {
    paddingVertical: spacing.md,
    marginRight: spacing.xl,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: colors.primary,
  },
  tabText: {
    ...type.headingMd,
    color: colors.textSecondary,
  },
  tabTextActive: {
    color: colors.primary,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: 100,
  },
  detailsTab: {
    gap: spacing.xl,
  },
  infoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.lg,
  },
  infoItem: {
    minWidth: '45%',
  },
  infoLabel: {
    ...type.label,
    color: colors.textSecondary,
    marginBottom: 4,
  },
  infoValue: {
    ...type.bodyLg,
    color: colors.textPrimary,
  },
  editableSection: {
    gap: spacing.lg,
  },
  sectionLabel: {
    ...type.label,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  stockEditRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
  },
  stockInput: {
    ...type.displayLg,
    color: colors.textPrimary,
    fontFamily: type.mono.fontFamily,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    minWidth: 120,
  },
  unitText: {
    ...type.headingMd,
    color: colors.textSecondary,
    paddingBottom: spacing.sm,
  },
  priceRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  priceInputGroup: {
    flex: 1,
  },
  priceInput: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    color: colors.textPrimary,
    ...type.bodyLg,
    fontFamily: type.mono.fontFamily,
  },
  deleteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    marginTop: spacing.xxl,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.danger + '40',
  },
  deleteBtnText: {
    ...type.bodySm,
    color: colors.danger,
    fontWeight: 'bold',
  },
  forecastTab: {
    gap: spacing.lg,
  },
  chartCard: {
    backgroundColor: colors.surface,
    padding: spacing.lg,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chartTitle: {
    ...type.headingMd,
    color: colors.textPrimary,
    marginBottom: spacing.xl,
  },
  forecastMetrics: {
    gap: spacing.md,
  },
  metricCard: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricTitle: {
    ...type.bodySm,
    color: colors.textSecondary,
  },
  metricValue: {
    ...type.headingMd,
    color: colors.textPrimary,
  },
  metricUnit: {
    ...type.label,
    color: colors.textSecondary,
    fontWeight: 'normal',
  },
  forecastBadges: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: radius.full,
  },
  badgeText: {
    ...type.label,
    fontWeight: 'bold',
  },
  saveFooter: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.bg,
    padding: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  saveBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  saveBtnText: {
    ...type.headingMd,
    color: colors.bg,
  },
});

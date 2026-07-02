import React, { useEffect, useState, useMemo } from 'react';
import { View, Text, StyleSheet, FlatList, Pressable, RefreshControl, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors, type, spacing, radius } from '../../constants/theme';
import api from '../../lib/api';

export default function ReorderAlerts() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [filter, setFilter] = useState('All'); // All | Low Stock | Out of Stock
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const res = await api.get('/alerts');
      setAlerts(res.data);
    } catch (err) {
      console.error("Alerts fetch error", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handleResolve = async (alertId: string, recommendedQty: number) => {
    try {
      // Backend expects POST with quantity_restocked payload
      await api.post(`/alerts/${alertId}/resolve`, {
        quantity_restocked: recommendedQty || 0
      });
      setAlerts(alerts.map((a: any) => a.alert_id === alertId ? { ...a, is_resolved: true } : a));
      Alert.alert("Success", "Alert resolved and inventory updated");
    } catch (err: any) {
      console.error("Resolve alert error:", err.response?.data);
      Alert.alert("Error", err.response?.data?.detail || "Failed to resolve alert");
    }
  };

  const filteredAlerts = useMemo(() => {
    const active = alerts.filter((a: any) => !a.is_resolved);
    if (filter === 'All') return active;
    const normalizedFilter = filter.toUpperCase().replace(' ', '_');
    return active.filter((a: any) => a.alert_type.toUpperCase() === normalizedFilter);
  }, [alerts, filter]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Reorder Alerts</Text>
        <View style={styles.filterRow}>
          {['All', 'Low Stock', 'Out of Stock'].map((f) => (
            <Pressable
              key={f}
              style={[
                styles.filterChip,
                filter === f && styles.filterChipActive
              ]}
              onPress={() => setFilter(f)}
            >
              <Text style={[
                styles.filterText,
                filter === f && styles.filterTextActive
              ]}>{f}</Text>
            </Pressable>
          ))}
        </View>
      </View>

      <FlatList
        data={filteredAlerts}
        keyExtractor={(item) => item.alert_id}
        renderItem={({ item }: { item: any }) => (
          <View style={styles.alertCard}>
            <View style={styles.alertHeader}>
              <View style={[styles.typeBadge, { backgroundColor: item.alert_type.toLowerCase() === 'out_of_stock' ? colors.danger + '20' : colors.warning + '20' }]}>
                <Text style={[styles.typeText, { color: item.alert_type.toLowerCase() === 'out_of_stock' ? colors.danger : colors.warning }]}>
                  {item.alert_type.replace('_', ' ').toUpperCase()}
                </Text>
              </View>
              <Text style={styles.dateText}>{new Date(item.created_at).toLocaleDateString()}</Text>
            </View>

            <Text style={styles.productName}>{item.product_name}</Text>
            
            <View style={styles.metaRow}>
              <View style={styles.metaItem}>
                <Text style={styles.metaLabel}>Current</Text>
                <Text style={styles.metaValue}>{item.current_stock}</Text>
              </View>
              <View style={styles.metaItem}>
                <Text style={styles.metaLabel}>Threshold</Text>
                <Text style={styles.metaValue}>{item.threshold}</Text>
              </View>
            </View>

            {item.recommended_qty > 0 && (
              <View style={styles.reorderInfo}>
                <MaterialCommunityIcons name="truck-delivery-outline" size={16} color={colors.primary} />
                <Text style={styles.reorderText}>
                  Recommended reorder: <Text style={{ color: colors.primary, fontWeight: 'bold' }}>{item.recommended_qty}</Text> units
                </Text>
              </View>
            )}

            <Pressable 
              style={styles.resolveBtn}
              onPress={() => handleResolve(item.alert_id, item.recommended_qty)}
            >
              <Text style={styles.resolveBtnText}>Mark Resolved</Text>
            </Pressable>
          </View>
        )}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <MaterialCommunityIcons name="check-circle-outline" size={48} color={colors.primary} />
            <Text style={styles.emptyText}>All caught up!</Text>
          </View>
        }
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
    paddingBottom: spacing.md,
  },
  title: {
    ...type.displaySm,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  filterRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  filterChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radius.full,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterText: {
    ...type.label,
    color: colors.textSecondary,
  },
  filterTextActive: {
    color: colors.bg,
    fontWeight: 'bold',
  },
  listContent: {
    padding: spacing.lg,
    paddingBottom: 50,
  },
  alertCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: radius.sm,
  },
  typeText: {
    ...type.label,
    fontWeight: 'bold',
    fontSize: 10,
  },
  dateText: {
    ...type.label,
    color: colors.textMuted,
  },
  productName: {
    ...type.headingMd,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  metaRow: {
    flexDirection: 'row',
    gap: spacing.xl,
    marginBottom: spacing.md,
  },
  metaItem: {
    gap: 2,
  },
  metaLabel: {
    ...type.label,
    color: colors.textSecondary,
  },
  metaValue: {
    ...type.headingMd,
    fontFamily: type.mono.fontFamily,
    color: colors.textPrimary,
  },
  reorderInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.primaryDim,
    padding: spacing.sm,
    borderRadius: radius.md,
    marginBottom: spacing.lg,
  },
  reorderText: {
    ...type.bodySm,
    color: colors.textSecondary,
  },
  resolveBtn: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  resolveBtnText: {
    ...type.bodySm,
    color: colors.textPrimary,
    fontWeight: 'bold',
  },
  emptyContainer: {
    marginTop: 100,
    alignItems: 'center',
    gap: spacing.sm,
  },
  emptyText: {
    ...type.bodySm,
    color: colors.textSecondary,
  },
});

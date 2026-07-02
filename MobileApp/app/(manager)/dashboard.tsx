import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, RefreshControl, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuthStore } from '../../stores/authStore';
import { colors, type, spacing, radius } from '../../constants/theme';
import api from '../../lib/api';

export default function ManagerDashboard() {
  const router = useRouter();
  const fullName = useAuthStore(state => state.fullName);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState({
    totalSkus: 0,
    lowStock: 0,
    outOfStock: 0,
    todaySales: 0,
  });
  const [alerts, setAlerts] = useState<any[]>([]);

  const fetchData = async () => {
    try {
      // Parallel fetch for dashboard data
      const [inventoryRes, alertsRes] = await Promise.all([
        api.get('/inventory/'),
        api.get('/alerts'),
      ]);

      const products = inventoryRes.data;
      const activeAlerts = alertsRes.data.filter((a: any) => !a.is_resolved);

      setStats({
        totalSkus: products.length,
        lowStock: products.filter((p: any) => p.current_stock > 0 && p.current_stock <= p.reorder_threshold).length,
        outOfStock: products.filter((p: any) => p.current_stock <= 0).length,
        todaySales: 0, 
      });

      setAlerts(activeAlerts.slice(0, 5));
    } catch (err) {
      console.error("Dashboard fetch error", err);
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

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Good morning,</Text>
          <Text style={styles.userName}>{fullName || 'Manager'} 👋</Text>
        </View>
        <View style={styles.headerActions}>
          <Pressable 
            style={styles.notifBtn}
            onPress={() => router.push('/(manager)/alerts')}
          >
            <MaterialCommunityIcons name="bell-outline" size={24} color={colors.textPrimary} />
            {stats.lowStock + stats.outOfStock > 0 && <View style={styles.notifBadge} />}
          </Pressable>
          <Pressable 
            style={[styles.notifBtn, { borderColor: colors.danger + '40' }]}
            onPress={() => {
              Alert.alert("Logout", "Are you sure you want to logout?", [
                { text: "Cancel", style: "cancel" },
                { text: "Logout", style: "destructive", onPress: async () => {
                  const { logout } = useAuthStore.getState();
                  logout();
                  router.replace('/');
                }}
              ]);
            }}
          >
            <MaterialCommunityIcons name="logout" size={24} color={colors.danger} />
          </Pressable>
        </View>
      </View>

      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.statsScroll}
      >
        <StatCard title="Total SKUs" value={stats.totalSkus.toString()} icon="package-variant" />
        <StatCard title="Low Stock" value={stats.lowStock.toString()} icon="alert-outline" color={colors.warning} />
        <StatCard title="Out of Stock" value={stats.outOfStock.toString()} icon="close-circle-outline" color={colors.danger} />
        <StatCard title="Today Sales" value={`₹${stats.todaySales}`} icon="currency-inr" color={colors.primary} />
      </ScrollView>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Needs Restock</Text>
          {alerts.length > 0 && (
            <View style={styles.countBadge}>
              <Text style={styles.countText}>{alerts.length}</Text>
            </View>
          )}
        </View>

        {alerts.length === 0 ? (
          <View style={styles.emptyAlerts}>
            <Text style={styles.emptyText}>All stock levels are healthy! 🎉</Text>
          </View>
        ) : (
          alerts.map((alert: any) => (
            <AlertCard key={alert.alert_id} alert={alert} />
          ))
        )}

        {alerts.length > 0 && (
          <Pressable 
            style={styles.viewAllBtn}
            onPress={() => router.push('/(manager)/alerts')}
          >
            <Text style={styles.viewAllText}>View All Alerts</Text>
          </Pressable>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsGrid}>
          <ActionBtn 
            title="Add Product" 
            icon="plus-box" 
            onPress={() => router.push('/(manager)/inventory/add')} 
          />
          <ActionBtn 
            title="Manage Staff" 
            icon="account-group" 
            onPress={() => router.push('/(manager)/staff/')} 
          />
          <ActionBtn 
            title="Open POS" 
            icon="cash-register" 
            onPress={() => router.push('/(cashier)/pos')} 
          />
        </View>
      </View>
      
      <View style={{ height: spacing.xxl }} />
    </ScrollView>
  );
}

function StatCard({ title, value, icon, color = colors.textSecondary }: any) {
  return (
    <View style={styles.statCard}>
      <View style={styles.statHeader}>
        <Text style={styles.statTitle}>{title}</Text>
        <MaterialCommunityIcons name={icon} size={20} color={color} />
      </View>
      <Text style={[styles.statValue, { color: color === colors.textSecondary ? colors.textPrimary : color }]}>{value}</Text>
    </View>
  );
}

function AlertCard({ alert }: any) {
  return (
    <View style={styles.alertCard}>
      <View style={styles.alertInfo}>
        <Text style={styles.alertProductName}>{alert.product_name}</Text>
        <Text style={styles.alertMeta}>Stock: {alert.current_stock} | Threshold: {alert.threshold}</Text>
      </View>
      <View style={[styles.alertBadge, { backgroundColor: alert.alert_type.toLowerCase() === 'out_of_stock' ? colors.danger + '20' : colors.warning + '20' }]}>
        <Text style={[styles.alertBadgeText, { color: alert.alert_type.toLowerCase() === 'out_of_stock' ? colors.danger : colors.warning }]}>
          {alert.alert_type.toLowerCase() === 'out_of_stock' ? 'OUT' : 'LOW'}
        </Text>
      </View>
    </View>
  );
}

function ActionBtn({ title, icon, onPress }: any) {
  return (
    <Pressable style={styles.actionBtn} onPress={onPress}>
      <MaterialCommunityIcons name={icon} size={32} color={colors.primary} />
      <Text style={styles.actionBtnText}>{title}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.lg,
  },
  headerActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  greeting: {
    ...type.bodySm,
    color: colors.textSecondary,
  },
  userName: {
    ...type.displaySm,
    color: colors.textPrimary,
  },
  notifBtn: {
    width: 44,
    height: 44,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  notifBadge: {
    position: 'absolute',
    top: 10,
    right: 12,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.danger,
    borderWidth: 1.5,
    borderColor: colors.surface,
  },
  statsScroll: {
    paddingLeft: spacing.lg,
    paddingRight: spacing.sm,
    paddingBottom: spacing.md,
    gap: spacing.md,
  },
  statCard: {
    width: 140,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  statHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  statTitle: {
    ...type.label,
    color: colors.textSecondary,
    flex: 1,
  },
  statValue: {
    ...type.headingMd,
    fontFamily: type.mono.fontFamily,
  },
  section: {
    paddingHorizontal: spacing.lg,
    marginTop: spacing.xl,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  sectionTitle: {
    ...type.headingMd,
    color: colors.textPrimary,
  },
  countBadge: {
    backgroundColor: colors.danger,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radius.full,
  },
  countText: {
    ...type.label,
    color: colors.textPrimary,
    fontSize: 10,
  },
  alertCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  alertInfo: {
    flex: 1,
  },
  alertProductName: {
    ...type.bodyLg,
    color: colors.textPrimary,
  },
  alertMeta: {
    ...type.bodySm,
    color: colors.textSecondary,
    fontFamily: type.mono.fontFamily,
  },
  alertBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: radius.sm,
  },
  alertBadgeText: {
    ...type.label,
    fontWeight: 'bold',
  },
  viewAllBtn: {
    alignItems: 'center',
    paddingVertical: spacing.md,
  },
  viewAllText: {
    ...type.bodySm,
    color: colors.primary,
    fontWeight: 'bold',
  },
  emptyAlerts: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.xl,
    alignItems: 'center',
    borderStyle: 'dashed',
    borderWidth: 1,
    borderColor: colors.border,
  },
  emptyText: {
    ...type.bodySm,
    color: colors.textSecondary,
  },
  actionsGrid: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  actionBtn: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    alignItems: 'center',
    gap: spacing.sm,
  },
  actionBtnText: {
    ...type.bodySm,
    color: colors.textPrimary,
    fontWeight: 'bold',
  },
});

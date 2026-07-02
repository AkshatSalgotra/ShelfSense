import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, Pressable, RefreshControl, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors, type, spacing, radius } from '../../../constants/theme';
import api from '../../../lib/api';

export default function StaffManagement() {
  const router = useRouter();
  const [staff, setStaff] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const res = await api.get('/staff');
      setStaff(res.data);
    } catch (err) {
      console.error("Staff fetch error", err);
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

  const handleDeactivate = async (userId: string, currentStatus: boolean) => {
    const action = currentStatus ? 'deactivate' : 'reactivate';
    Alert.alert(
      `${action.charAt(0).toUpperCase() + action.slice(1)} Staff`,
      `Are you sure you want to ${action} this staff member?`,
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: action.toUpperCase(), 
          style: currentStatus ? "destructive" : "default",
          onPress: async () => {
            try {
              await api.patch(`/staff/${userId}/${action}`);
              fetchData();
            } catch (err) {
              Alert.alert("Error", `Failed to ${action} staff`);
            }
          }
        }
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Staff Management</Text>
      </View>

      <FlatList
        data={staff}
        keyExtractor={(item) => item.user_id}
        renderItem={({ item }: { item: any }) => (
          <View style={[styles.staffCard, !item.is_active && styles.staffCardInactive]}>
            <View style={styles.staffInfo}>
              <View style={styles.avatar}>
                <MaterialCommunityIcons name="account" size={32} color={item.is_active ? colors.primary : colors.textMuted} />
              </View>
              <View>
                <Text style={[styles.staffName, !item.is_active && { color: colors.textSecondary }]}>
                  {item.full_name}
                </Text>
                <Text style={styles.staffPhone}>📱 {item.phone}</Text>
              </View>
            </View>

            <View style={styles.cardActions}>
              <View style={styles.statusRow}>
                <View style={[styles.statusDot, { backgroundColor: item.is_active ? colors.primary : colors.danger }]} />
                <Text style={[styles.statusText, { color: item.is_active ? colors.primary : colors.danger }]}>
                  {item.is_active ? 'Active' : 'Inactive'}
                </Text>
              </View>
              
              <Pressable 
                style={[styles.actionBtn, item.is_active ? styles.btnDeactivate : styles.btnReactivate]}
                onPress={() => handleDeactivate(item.user_id, item.is_active)}
              >
                <Text style={[styles.actionBtnText, { color: item.is_active ? colors.danger : colors.primary }]}>
                  {item.is_active ? 'Deactivate' : 'Reactivate'}
                </Text>
              </Pressable>
            </View>
          </View>
        )}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <MaterialCommunityIcons name="account-search-outline" size={48} color={colors.textMuted} />
            <Text style={styles.emptyText}>No cashiers found</Text>
          </View>
        }
      />

      <Pressable 
        style={styles.fab}
        onPress={() => router.push('/(manager)/staff/add')}
      >
        <MaterialCommunityIcons name="plus" size={32} color={colors.bg} />
      </Pressable>
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
  },
  listContent: {
    padding: spacing.lg,
    paddingBottom: 100,
  },
  staffCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  staffCardInactive: {
    opacity: 0.6,
  },
  staffInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.bg,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  staffName: {
    ...type.headingMd,
    color: colors.textPrimary,
  },
  staffPhone: {
    ...type.bodySm,
    color: colors.textSecondary,
    fontFamily: type.mono.fontFamily,
    marginTop: 2,
  },
  cardActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.md,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    ...type.label,
    fontWeight: 'bold',
  },
  actionBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radius.md,
    borderWidth: 1,
  },
  btnDeactivate: {
    borderColor: colors.danger + '40',
  },
  btnReactivate: {
    borderColor: colors.primary + '40',
  },
  actionBtnText: {
    ...type.label,
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
  fab: {
    position: 'absolute',
    bottom: spacing.xl,
    right: spacing.xl,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
});

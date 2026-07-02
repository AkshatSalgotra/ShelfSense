import React, { useEffect, useState, useMemo } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, Pressable, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors, type, spacing, radius } from '../../../constants/theme';
import api from '../../../lib/api';
import ProductListItem from '../../../components/ProductListItem';

export default function InventoryList() {
  const router = useRouter();
  const [products, setProducts] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All'); // All | Low Stock | Out of Stock
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const res = await api.get('/inventory/');
      setProducts(res.data);
    } catch (err) {
      console.error("Inventory fetch error", err);
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

  const filteredProducts = useMemo(() => {
    return products.filter((p: any) => {
      const matchesSearch = p.product_name.toLowerCase().includes(search.toLowerCase()) || 
                            (p.sku_code && p.sku_code.toLowerCase().includes(search.toLowerCase()));
      
      if (!matchesSearch) return false;

      if (filter === 'Low Stock') {
        return p.current_stock > 0 && p.current_stock <= (p.reorder_threshold || 10);
      }
      if (filter === 'Out of Stock') {
        return p.current_stock === 0;
      }
      return true;
    });
  }, [products, search, filter]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Inventory</Text>
        <View style={styles.searchContainer}>
          <MaterialCommunityIcons name="magnify" size={20} color={colors.textSecondary} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search name or SKU..."
            placeholderTextColor={colors.textMuted}
            value={search}
            onChangeText={setSearch}
          />
        </View>

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
        data={filteredProducts}
        keyExtractor={(item) => item.product_id}
        renderItem={({ item }: { item: any }) => (
          <ProductListItem 
            product={item} 
            onPress={() => router.push(`/(manager)/inventory/${item.product_id}`)} 
          />
        )}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <MaterialCommunityIcons name="package-variant" size={48} color={colors.textMuted} />
            <Text style={styles.emptyText}>No products found</Text>
          </View>
        }
      />

      <Pressable 
        style={styles.fab}
        onPress={() => router.push('/(manager)/inventory/add')}
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
    backgroundColor: colors.bg,
  },
  title: {
    ...type.displaySm,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    height: 44,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  searchInput: {
    flex: 1,
    marginLeft: spacing.sm,
    color: colors.textPrimary,
    ...type.bodySm,
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
    paddingBottom: 100,
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

import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { colors, type, spacing, radius } from '../constants/theme';

export interface Product {
  id: string;
  product_name: string;
  category?: string;
  sku_code?: string;
  current_stock: number;
  reorder_threshold: number;
  cost_price?: number;
  selling_price: number;
  unit?: string;
}

interface ProductListItemProps {
  product: Product;
  onPress?: () => void;
}

export default function ProductListItem({ product, onPress }: ProductListItemProps) {
  const threshold = product.reorder_threshold || 10;
  const isLowStock = product.current_stock <= threshold;
  const isOutOfStock = product.current_stock === 0;

  let stockColor = colors.primary;
  if (isOutOfStock) stockColor = colors.danger;
  else if (isLowStock) stockColor = colors.warning;

  const stockPercent = Math.min((product.current_stock / (threshold * 2)) * 100, 100);

  return (
    <Pressable 
      style={({ pressed }) => [styles.container, pressed && { opacity: 0.75 }]}
      onPress={onPress}
    >
      <View style={styles.header}>
        <Text style={styles.name} numberOfLines={1}>{product.product_name}</Text>
        {product.category && (
          <View style={styles.categoryBadge}>
            <Text style={styles.categoryText}>{product.category}</Text>
          </View>
        )}
      </View>
      
      <Text style={styles.sku}>SKU: {product.sku_code || 'N/A'}</Text>

      <View style={styles.footer}>
        <View style={styles.stockInfo}>
          <Text style={styles.stockText}>
            Stock: <Text style={{ color: colors.textPrimary, fontFamily: type.mono.fontFamily }}>{product.current_stock}</Text> units
          </Text>
          <Text style={styles.priceText}>₹{product.selling_price}</Text>
        </View>

        <View style={styles.progressBarBg}>
          <View style={[styles.progressBarFill, { width: `${stockPercent}%`, backgroundColor: stockColor }]} />
        </View>
        
        <Text style={styles.thresholdText}>Threshold: {threshold}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  name: {
    ...type.headingMd,
    color: colors.textPrimary,
    flex: 1,
  },
  categoryBadge: {
    backgroundColor: colors.primaryDim,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radius.sm,
    marginLeft: spacing.sm,
  },
  categoryText: {
    ...type.label,
    color: colors.primary,
    fontSize: 10,
  },
  sku: {
    ...type.bodySm,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  footer: {
    gap: spacing.xs,
  },
  stockInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  stockText: {
    ...type.bodySm,
    color: colors.textSecondary,
  },
  priceText: {
    ...type.bodyLg,
    color: colors.textPrimary,
    fontWeight: 'bold',
  },
  progressBarBg: {
    height: 6,
    backgroundColor: colors.border,
    borderRadius: radius.full,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: radius.full,
  },
  thresholdText: {
    ...type.label,
    color: colors.textMuted,
    textAlign: 'right',
    marginTop: 2,
  },
});

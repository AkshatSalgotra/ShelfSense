import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, radius, spacing, type } from '../constants/theme';

export type StockStatus = 'CRITICAL' | 'WARNING' | 'HEALTHY';

interface StockBadgeProps {
  status: StockStatus;
  compact?: boolean;
}

const STATUS_CONFIG = {
  CRITICAL: { label: 'Critical', bg: colors.danger + '20', text: colors.danger },
  WARNING:  { label: 'Warning',  bg: colors.warning + '20',  text: colors.warning  },
  HEALTHY:  { label: 'Healthy',  bg: colors.primaryDim,  text: colors.primary  },
};

export default function StockBadge({ status, compact }: StockBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.HEALTHY;

  return (
    <View style={[styles.badge, { backgroundColor: config.bg }]}>
      <View style={[styles.dot, { backgroundColor: config.text }]} />
      {!compact && <Text style={[styles.label, { color: config.text }]}>{config.label}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.full,
    gap: spacing.xs,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  label: {
    ...type.label,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
});

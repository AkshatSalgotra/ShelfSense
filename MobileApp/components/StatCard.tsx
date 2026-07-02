import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, type, spacing, radius, shadow } from '../constants/theme';
import { LinearGradient } from 'expo-linear-gradient';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
  gradient?: readonly [string, string, ...string[]];
}

export default function StatCard({ title, value, subtitle, icon, color, gradient }: StatCardProps) {
  const Wrapper = gradient ? LinearGradient : View;
  const wrapperProps = gradient
    ? { colors: gradient, start: { x: 0, y: 0 }, end: { x: 1, y: 1 } }
    : {};

  return (
    <Wrapper style={[styles.card, shadow.sm]} {...(wrapperProps as any)}>
      <View style={styles.header}>
        <View style={[styles.iconContainer, { backgroundColor: color ? `${color}20` : colors.primaryDim }]}>
          {icon}
        </View>
      </View>
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.title}>{title}</Text>
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
    </Wrapper>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
    flex: 1,
    minWidth: 140,
  },
  header: {
    marginBottom: spacing.md,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  value: {
    ...type.displaySm,
    color: colors.textPrimary,
    marginBottom: 2,
    fontFamily: type.mono.fontFamily,
  },
  title: {
    ...type.label,
    color: colors.textSecondary,
  },
  subtitle: {
    ...type.bodySm,
    color: colors.textMuted,
    marginTop: 2,
  },
});

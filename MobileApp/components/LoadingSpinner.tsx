import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { colors, spacing, type } from '../constants/theme';

interface LoadingSpinnerProps {
  message?: string;
  fullscreen?: boolean;
}

export default function LoadingSpinner({ message, fullscreen }: LoadingSpinnerProps) {
  return (
    <View style={[styles.container, fullscreen && styles.fullscreen]}>
      <ActivityIndicator size="large" color={colors.primary} />
      {message && <Text style={styles.message}>{message}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xxl,
  },
  fullscreen: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  message: {
    ...type.bodySm,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
});

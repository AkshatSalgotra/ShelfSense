import React from 'react';
import { Pressable, Text, StyleSheet, ActivityIndicator, PressableProps, ViewStyle, TextStyle } from 'react-native';
import { colors, type, spacing, radius } from '../constants/theme';

interface ButtonProps extends PressableProps {
  title: string;
  variant?: 'primary' | 'danger' | 'outline';
  loading?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export function Button({ title, variant = 'primary', loading = false, style, textStyle, disabled, ...props }: ButtonProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return { bg: colors.danger, text: colors.textPrimary };
      case 'outline':
        return { bg: 'transparent', text: colors.primary, border: colors.primary };
      case 'primary':
      default:
        return { bg: colors.primary, text: colors.bg };
    }
  };

  const vStyles = getVariantStyles();

  return (
    <Pressable
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: vStyles.bg },
        vStyles.border && { borderWidth: 1, borderColor: vStyles.border },
        disabled && styles.disabled,
        pressed && !disabled && { opacity: 0.75 },
        style,
      ]}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <ActivityIndicator color={vStyles.text} />
      ) : (
        <Text style={[styles.text, { color: vStyles.text }, textStyle]}>
          {title}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    ...type.label,
    fontSize: 16,
    fontFamily: 'Syne_600SemiBold',
  },
  disabled: {
    opacity: 0.5,
  },
});

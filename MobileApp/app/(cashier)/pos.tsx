import React, { useEffect, useState, useMemo } from 'react';
import { 
  View, Text, StyleSheet, FlatList, TextInput, 
  Pressable, ActivityIndicator, Alert, ScrollView 
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuthStore } from '../../stores/authStore';
import { useCartStore } from '../../stores/cartStore';
import { colors, type, spacing, radius } from '../../constants/theme';
import api from '../../lib/api';
// import RazorpayCheckout from 'react-native-razorpay';

export default function POSScreen() {
  const router = useRouter();
  const { fullName, logout } = useAuthStore();
  const { items, addItem, removeItem, updateQty, clearCart, total } = useCartStore();
  
  const [products, setProducts] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [checkingOut, setCheckingOut] = useState(false);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const res = await api.get('/inventory/');
      setProducts(res.data);
    } catch (err) {
      console.error("POS fetch products error", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = useMemo(() => {
    if (!search) return [];
    return products.filter((p: any) => 
      p.product_name.toLowerCase().includes(search.toLowerCase()) || 
      (p.sku_code && p.sku_code.toLowerCase().includes(search.toLowerCase()))
    ).slice(0, 10);
  }, [products, search]);

  const handleCheckout = async () => {
    if (items.length === 0) return;

    setCheckingOut(true);
    try {
      const orderData = {
        items: items.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity
        }))
      };

      const res = await api.post('/orders', orderData);
      const { razorpay_order_id, amount_paise, key_id, order_number } = res.data;

      const options = {
        description: `Order #${order_number}`,
        image: 'https://i.imgur.com/399499X.png',
        currency: 'INR',
        key: key_id,
        amount: amount_paise,
        name: 'ShelfSense',
        order_id: razorpay_order_id,
        prefill: {
          email: '',
          contact: '',
          name: fullName
        },
        theme: { color: colors.primary }
      };

      /*
      RazorpayCheckout.open(options).then(async (data: any) => {
        // Verification
        try {
          await api.post('/payments/verify', {
            razorpay_payment_id: data.razorpay_payment_id,
            razorpay_order_id: data.razorpay_order_id,
            razorpay_signature: data.razorpay_signature
          });
          
          clearCart();
          Alert.alert("Success", "Payment verified and order placed! 🎉");
        } catch (vErr) {
          Alert.alert("Verification Failed", "Payment was successful but we couldn't verify it. Please contact manager.");
        }
      }).catch((error: any) => {
        Alert.alert("Payment Failed", error.description || "Payment cancelled");
      });
      */

      // TEMP: Auto-success for Expo Go testing
      clearCart();
      Alert.alert("Success (Simulated)", "Order placed successfully! (Razorpay is disabled for Expo Go)");

    } catch (err: any) {
      console.error("Order creation error:", err.response?.data);
      const errorMsg = err.response?.data?.detail || "Failed to create order";
      Alert.alert("Error", typeof errorMsg === 'string' ? errorMsg : "Check product stock or Razorpay config");
    } finally {
      setCheckingOut(false);
    }
  };

  const handleLogout = () => {
    Alert.alert("Logout", "Are you sure you want to logout?", [
      { text: "Cancel", style: "cancel" },
      { text: "Logout", onPress: () => {
        logout();
        router.replace('/');
      }}
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.logoText}>ShelfSense</Text>
        <View style={styles.headerRight}>
          <Text style={styles.cashierName}>{fullName || 'Cashier'}</Text>
          <Pressable onPress={handleLogout}>
            <MaterialCommunityIcons name="logout" size={20} color={colors.danger} />
          </Pressable>
        </View>
      </View>

      <View style={styles.searchSection}>
        <View style={styles.searchBar}>
          <MaterialCommunityIcons name="magnify" size={20} color={colors.textSecondary} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search products..."
            placeholderTextColor={colors.textMuted}
            value={search}
            onChangeText={setSearch}
          />
          {search.length > 0 && (
            <Pressable onPress={() => setSearch('')}>
              <MaterialCommunityIcons name="close-circle" size={20} color={colors.textMuted} />
            </Pressable>
          )}
        </View>

        {search.length > 0 && (
          <View style={styles.resultsList}>
            {filteredProducts.length === 0 ? (
              <Text style={styles.noResults}>No products found</Text>
            ) : (
              filteredProducts.map((p: any) => (
                <Pressable 
                  key={p.product_id} 
                  style={styles.resultItem}
                  onPress={() => {
                    addItem({ product_id: p.product_id, product_name: p.product_name, selling_price: p.selling_price });
                    setSearch('');
                  }}
                >
                  <View style={{ flex: 1 }}>
                    <Text style={styles.resultName}>{p.product_name}</Text>
                    <Text style={styles.resultMeta}>₹{p.selling_price} | Stock: {p.current_stock}</Text>
                  </View>
                  <View style={styles.addBtn}>
                    <MaterialCommunityIcons name="plus" size={20} color={colors.primary} />
                    <Text style={styles.addBtnText}>Add</Text>
                  </View>
                </Pressable>
              ))
            )}
          </View>
        )}
      </View>

      <View style={styles.cartSection}>
        <View style={styles.cartHeader}>
          <Text style={styles.cartTitle}>CART</Text>
          <Text style={styles.cartCount}>{items.length} items</Text>
        </View>

        <FlatList
          data={items}
          keyExtractor={(item) => item.product_id}
          renderItem={({ item }: { item: any }) => (
            <View style={styles.cartItem}>
              <View style={{ flex: 1 }}>
                <Text style={styles.cartItemName}>{item.product_name}</Text>
                <Text style={styles.cartItemPrice}>₹{item.selling_price * item.quantity} (₹{item.selling_price} × {item.quantity})</Text>
              </View>
              <View style={styles.qtyRow}>
                <Pressable 
                  style={styles.qtyBtn} 
                  onPress={() => updateQty(item.product_id, item.quantity - 1)}
                >
                  <MaterialCommunityIcons name="minus" size={16} color={colors.textPrimary} />
                </Pressable>
                <Text style={styles.qtyText}>{item.quantity}</Text>
                <Pressable 
                  style={styles.qtyBtn} 
                  onPress={() => updateQty(item.product_id, item.quantity + 1)}
                >
                  <MaterialCommunityIcons name="plus" size={16} color={colors.textPrimary} />
                </Pressable>
              </View>
            </View>
          )}
          ListEmptyComponent={
            <View style={styles.emptyCart}>
              <MaterialCommunityIcons name="cart-outline" size={48} color={colors.textMuted} />
              <Text style={styles.emptyCartText}>Cart is empty. Search products to add.</Text>
            </View>
          }
        />

        <View style={styles.footer}>
          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Total</Text>
            <Text style={styles.totalValue}>₹{total()}</Text>
          </View>

          <Pressable 
            style={[styles.checkoutBtn, (items.length === 0 || checkingOut) && { opacity: 0.6 }]}
            onPress={handleCheckout}
            disabled={items.length === 0 || checkingOut}
          >
            {checkingOut ? (
              <ActivityIndicator color={colors.bg} />
            ) : (
              <Text style={styles.checkoutBtnText}>PROCEED TO PAYMENT</Text>
            )}
          </Pressable>
        </View>
      </View>
    </View>
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
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  logoText: {
    ...type.headingMd,
    color: colors.primary,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  cashierName: {
    ...type.bodySm,
    color: colors.textSecondary,
  },
  searchSection: {
    padding: spacing.lg,
    zIndex: 10,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    height: 48,
    borderWidth: 1,
    borderColor: colors.border,
  },
  searchInput: {
    flex: 1,
    marginLeft: spacing.sm,
    color: colors.textPrimary,
    ...type.bodySm,
  },
  resultsList: {
    position: 'absolute',
    top: 64,
    left: spacing.lg,
    right: spacing.lg,
    backgroundColor: colors.surfaceHigh,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    maxHeight: 300,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  noResults: {
    padding: spacing.md,
    color: colors.textMuted,
    textAlign: 'center',
  },
  resultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  resultName: {
    ...type.bodyLg,
    color: colors.textPrimary,
  },
  resultMeta: {
    ...type.label,
    color: colors.textSecondary,
    fontFamily: type.mono.fontFamily,
  },
  addBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryDim,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: radius.sm,
  },
  addBtnText: {
    ...type.label,
    color: colors.primary,
    fontWeight: 'bold',
  },
  cartSection: {
    flex: 1,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  cartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    backgroundColor: colors.surface,
  },
  cartTitle: {
    ...type.label,
    color: colors.textMuted,
    letterSpacing: 1,
  },
  cartCount: {
    ...type.label,
    color: colors.textSecondary,
  },
  cartItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  cartItemName: {
    ...type.bodyLg,
    color: colors.textPrimary,
  },
  cartItemPrice: {
    ...type.bodySm,
    color: colors.textSecondary,
    fontFamily: type.mono.fontFamily,
  },
  qtyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.bg,
    borderRadius: radius.md,
    padding: 4,
  },
  qtyBtn: {
    width: 28,
    height: 28,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    justifyContent: 'center',
    alignItems: 'center',
  },
  qtyText: {
    ...type.bodyLg,
    color: colors.textPrimary,
    fontFamily: type.mono.fontFamily,
    minWidth: 20,
    textAlign: 'center',
  },
  emptyCart: {
    marginTop: 50,
    alignItems: 'center',
    gap: spacing.sm,
  },
  emptyCartText: {
    ...type.bodySm,
    color: colors.textMuted,
    textAlign: 'center',
    paddingHorizontal: 50,
  },
  footer: {
    padding: spacing.xl,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  totalLabel: {
    ...type.headingMd,
    color: colors.textSecondary,
  },
  totalValue: {
    ...type.displaySm,
    color: colors.textPrimary,
    fontFamily: type.mono.fontFamily,
  },
  checkoutBtn: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.lg,
    alignItems: 'center',
  },
  checkoutBtnText: {
    ...type.headingMd,
    color: colors.bg,
    fontWeight: 'bold',
  },
});

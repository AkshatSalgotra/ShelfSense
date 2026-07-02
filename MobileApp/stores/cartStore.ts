import { create } from 'zustand';

export interface CartItem {
  product_id: string;
  product_name: string;
  selling_price: number;
  quantity: number;
}

interface CartState {
  items: CartItem[];
  addItem: (product: { product_id: string; product_name: string; selling_price: number }) => void;
  removeItem: (product_id: string) => void;
  updateQty: (product_id: string, quantity: number) => void;
  clearCart: () => void;
  total: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  addItem: (product) => set((state) => {
    const existing = state.items.find((i) => i.product_id === product.product_id);
    if (existing) {
      return {
        items: state.items.map((i) =>
          i.product_id === product.product_id ? { ...i, quantity: i.quantity + 1 } : i
        ),
      };
    }
    return { items: [...state.items, { ...product, quantity: 1 }] };
  }),
  removeItem: (product_id) => set((state) => ({
    items: state.items.filter((i) => i.product_id !== product_id),
  })),
  updateQty: (product_id, quantity) => set((state) => {
    if (quantity <= 0) {
      return { items: state.items.filter((i) => i.product_id !== product_id) };
    }
    return {
      items: state.items.map((i) => (i.product_id === product_id ? { ...i, quantity } : i)),
    };
  }),
  clearCart: () => set({ items: [] }),
  total: () => get().items.reduce((sum, i) => sum + i.selling_price * i.quantity, 0),
}));

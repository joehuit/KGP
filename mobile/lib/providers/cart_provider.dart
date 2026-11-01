import 'package:flutter/foundation.dart';
import '../models/cart_item.dart';
import '../models/product.dart';
import '../services/cart_storage_service.dart';

/// Provider managing local shopping cart state with persistent disk storage.
class CartProvider extends ChangeNotifier {
  List<CartItem> _items = [];
  bool _isLoaded = false;

  CartProvider() {
    _loadFromStorage();
  }

  List<CartItem> get items => List.unmodifiable(_items);
  bool get isLoaded => _isLoaded;
  bool get isEmpty => _items.isEmpty;

  /// Total financial amount in Algerian Dinars.
  double get totalAmount {
    return _items.fold(0.0, (sum, item) => sum + item.totalPrice);
  }

  /// Total quantity count of pieces in cart.
  int get totalItemsCount {
    return _items.fold(0, (count, item) => count + item.quantity);
  }

  /// Check if a product is already present in cart.
  bool containsProduct(int productId) {
    return _items.any((item) => item.product.id == productId);
  }

  /// Get the current quantity of a product in cart.
  int getQuantity(int productId) {
    final idx = _items.indexWhere((item) => item.product.id == productId);
    return idx != -1 ? _items[idx].quantity : 0;
  }

  Future<void> _loadFromStorage() async {
    try {
      _items = await CartStorageService.loadCart();
    } catch (_) {
      _items = [];
    } finally {
      _isLoaded = true;
      notifyListeners();
    }
  }

  Future<void> _persist() async {
    await CartStorageService.saveCart(_items);
  }

  /// Add product to cart or increment quantity if already added.
  void addItem(Product product, {int quantity = 1}) {
    if (quantity <= 0) return;

    final existingIndex = _items.indexWhere((item) => item.product.id == product.id);

    if (existingIndex != -1) {
      final currentQty = _items[existingIndex].quantity;
      int newQty = currentQty + quantity;

      // Bound to available stock if known
      if (product.availableQuantity != null && newQty > product.availableQuantity!) {
        newQty = product.availableQuantity!;
      }

      _items[existingIndex].quantity = newQty;
    } else {
      int initialQty = quantity;
      if (product.availableQuantity != null && initialQty > product.availableQuantity!) {
        initialQty = product.availableQuantity!;
      }
      _items.add(CartItem(product: product, quantity: initialQty));
    }

    notifyListeners();
    _persist();
  }

  /// Update item quantity directly. Removes item if quantity reaches 0.
  void updateQuantity(int productId, int quantity) {
    final index = _items.indexWhere((item) => item.product.id == productId);
    if (index == -1) return;

    if (quantity <= 0) {
      _items.removeAt(index);
    } else {
      final prod = _items[index].product;
      int clampedQty = quantity;
      if (prod.availableQuantity != null && clampedQty > prod.availableQuantity!) {
        clampedQty = prod.availableQuantity!;
      }
      _items[index].quantity = clampedQty;
    }

    notifyListeners();
    _persist();
  }

  /// Remove item completely from cart.
  void removeItem(int productId) {
    _items.removeWhere((item) => item.product.id == productId);
    notifyListeners();
    _persist();
  }

  /// Clear all cart contents upon successful checkout.
  void clear() {
    _items.clear();
    notifyListeners();
    CartStorageService.clearCart();
  }
}

import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants/app_constants.dart';
import '../models/cart_item.dart';
import '../models/guest_order.dart';

/// Service to persist shopping cart items and placed guest orders locally.
class CartStorageService {
  /// Save current cart items to device storage.
  static Future<void> saveCart(List<CartItem> items) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonList = items.map((item) => item.toJson()).toList();
    await prefs.setString(AppConstants.cartStorageKey, jsonEncode(jsonList));
  }

  /// Load persisted cart items from device storage.
  static Future<List<CartItem>> loadCart() async {
    final prefs = await SharedPreferences.getInstance();
    final rawJson = prefs.getString(AppConstants.cartStorageKey);
    if (rawJson == null || rawJson.isEmpty) return [];

    try {
      final decoded = jsonDecode(rawJson) as List<dynamic>;
      return decoded.map((item) => CartItem.fromJson(item as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }

  /// Clear saved cart upon successful order placement.
  static Future<void> clearCart() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.cartStorageKey);
  }

  /// Save placed guest order reference & tracking token to device order history.
  static Future<void> saveGuestOrderSummary(GuestOrderResponse order) async {
    final prefs = await SharedPreferences.getInstance();
    final rawJson = prefs.getString(AppConstants.savedOrdersStorageKey);
    List<Map<String, dynamic>> ordersList = [];

    if (rawJson != null && rawJson.isNotEmpty) {
      try {
        final decoded = jsonDecode(rawJson) as List<dynamic>;
        ordersList = decoded.cast<Map<String, dynamic>>();
      } catch (_) {
        ordersList = [];
      }
    }

    // Prepend latest order
    ordersList.insert(0, {
      'order_reference': order.orderReference,
      'tracking_token': order.trackingToken,
      'total_amount': order.totalAmount,
      'created_at': order.createdAt.toIso8601String(),
      'status': order.status,
    });

    // Keep up to 30 recent orders
    if (ordersList.length > 30) {
      ordersList = ordersList.sublist(0, 30);
    }

    await prefs.setString(AppConstants.savedOrdersStorageKey, jsonEncode(ordersList));
  }

  /// Retrieve list of recent local guest order summaries.
  static Future<List<Map<String, dynamic>>> loadSavedGuestOrders() async {
    final prefs = await SharedPreferences.getInstance();
    final rawJson = prefs.getString(AppConstants.savedOrdersStorageKey);
    if (rawJson == null || rawJson.isEmpty) return [];

    try {
      final decoded = jsonDecode(rawJson) as List<dynamic>;
      return decoded.cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }
}

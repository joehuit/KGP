import 'package:flutter/foundation.dart';
import '../models/guest_order.dart';
import '../services/api_service.dart';
import '../services/cart_storage_service.dart';
import 'cart_provider.dart';

/// Provider handling guest order placement and tracking operations.
class OrderProvider extends ChangeNotifier {
  final ApiService apiService;

  bool _isSubmitting = false;
  String? _submitError;
  GuestOrderResponse? _latestOrder;
  List<Map<String, dynamic>> _savedOrders = [];

  OrderProvider({required this.apiService}) {
    loadSavedOrders();
  }

  bool get isSubmitting => _isSubmitting;
  String? get submitError => _submitError;
  GuestOrderResponse? get latestOrder => _latestOrder;
  List<Map<String, dynamic>> get savedOrders => List.unmodifiable(_savedOrders);

  Future<void> loadSavedOrders() async {
    _savedOrders = await CartStorageService.loadSavedGuestOrders();
    notifyListeners();
  }

  /// Submit frictionless guest checkout order.
  Future<GuestOrderResponse?> submitGuestOrder(
    GuestOrderRequest request,
    CartProvider cart, {
    String? idempotencyKey,
  }) async {
    _isSubmitting = true;
    _submitError = null;
    notifyListeners();

    try {
      final response = await apiService.submitGuestOrder(request, idempotencyKey: idempotencyKey);
      _latestOrder = response;

      // Clear cart upon successful order creation
      cart.clear();

      // Save summary locally so user can track it
      await CartStorageService.saveGuestOrderSummary(response);
      await loadSavedOrders();

      return response;
    } catch (e) {
      _submitError = e.toString();
      return null;
    } finally {
      _isSubmitting = false;
      notifyListeners();
    }
  }

  /// Track order by secure token.
  Future<GuestOrderResponse> trackOrder(String trackingToken) async {
    return await apiService.trackGuestOrder(trackingToken);
  }
}

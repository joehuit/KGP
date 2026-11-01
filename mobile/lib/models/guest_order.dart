/// Line item in a guest order request.
class OrderItemRequest {
  final int productId;
  final int quantity;

  OrderItemRequest({
    required this.productId,
    required this.quantity,
  });

  Map<String, dynamic> toJson() {
    return {
      'product_id': productId,
      'quantity': quantity,
    };
  }
}

/// Guest order submission payload matching backend POST /api/v1/orders/guest.
class GuestOrderRequest {
  final String fullName;
  final String phoneNumber;
  final String wilaya;
  final String commune;
  final String deliveryAddress;
  final String? customerNotes;
  final List<OrderItemRequest> items;

  GuestOrderRequest({
    required this.fullName,
    required this.phoneNumber,
    required this.wilaya,
    required this.commune,
    required this.deliveryAddress,
    this.customerNotes,
    required this.items,
  });

  Map<String, dynamic> toJson() {
    return {
      'full_name': fullName,
      'phone_number': phoneNumber,
      'wilaya': wilaya,
      'commune': commune,
      'delivery_address': deliveryAddress,
      if (customerNotes != null && customerNotes!.trim().isNotEmpty)
        'customer_notes': customerNotes!.trim(),
      'items': items.map((i) => i.toJson()).toList(),
    };
  }
}

/// Frozen snapshot of an item from a submitted order.
class OrderItemSnapshot {
  final int id;
  final int? productId;
  final String productName;
  final String productSku;
  final double unitPrice;
  final int quantity;
  final double totalPrice;

  OrderItemSnapshot({
    required this.id,
    this.productId,
    required this.productName,
    required this.productSku,
    required this.unitPrice,
    required this.quantity,
    required this.totalPrice,
  });

  factory OrderItemSnapshot.fromJson(Map<String, dynamic> json) {
    double parsePrice(dynamic val) {
      if (val is num) return val.toDouble();
      if (val is String) return double.tryParse(val) ?? 0.0;
      return 0.0;
    }

    return OrderItemSnapshot(
      id: json['id'] as int,
      productId: json['product_id'] as int?,
      productName: json['product_name'] as String,
      productSku: json['product_sku'] as String,
      unitPrice: parsePrice(json['unit_price']),
      quantity: json['quantity'] as int,
      totalPrice: parsePrice(json['total_price']),
    );
  }
}

/// Guest order response received from backend with order reference and tracking token.
class GuestOrderResponse {
  final int id;
  final String orderReference;
  final String trackingToken;
  final String status;
  final double totalAmount;
  final String customerName;
  final String customerPhoneMasked;
  final String wilaya;
  final String commune;
  final String deliveryAddress;
  final String? customerNotes;
  final List<OrderItemSnapshot> items;
  final DateTime createdAt;

  GuestOrderResponse({
    required this.id,
    required this.orderReference,
    required this.trackingToken,
    required this.status,
    required this.totalAmount,
    required this.customerName,
    required this.customerPhoneMasked,
    required this.wilaya,
    required this.commune,
    required this.deliveryAddress,
    this.customerNotes,
    required this.items,
    required this.createdAt,
  });

  String get localizedStatus {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return 'قيد المراجعة (En attente)';
      case 'CONFIRMED':
        return 'تم التأكيد (Confirmée)';
      case 'PROCESSING':
        return 'قيد التحضير (En préparation)';
      case 'SHIPPED':
        return 'تم الشحن (Expédiée)';
      case 'DELIVERED':
        return 'تم التسليم (Livrée)';
      case 'CANCELLED':
        return 'ملغاة (Annulée)';
      default:
        return status;
    }
  }

  factory GuestOrderResponse.fromJson(Map<String, dynamic> json) {
    double parsePrice(dynamic val) {
      if (val is num) return val.toDouble();
      if (val is String) return double.tryParse(val) ?? 0.0;
      return 0.0;
    }

    return GuestOrderResponse(
      id: json['id'] as int,
      orderReference: json['order_reference'] as String,
      trackingToken: json['tracking_token'] as String? ?? '',
      status: json['status'] as String,
      totalAmount: parsePrice(json['total_amount']),
      customerName: json['customer_name'] as String? ?? '',
      customerPhoneMasked: json['customer_phone_masked'] as String? ?? '',
      wilaya: json['wilaya'] as String? ?? '',
      commune: json['commune'] as String? ?? '',
      deliveryAddress: json['delivery_address'] as String? ?? '',
      customerNotes: json['customer_notes'] as String?,
      items: (json['items'] as List<dynamic>? ?? [])
          .map((item) => OrderItemSnapshot.fromJson(item as Map<String, dynamic>))
          .toList(),
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'order_reference': orderReference,
      'tracking_token': trackingToken,
      'status': status,
      'total_amount': totalAmount,
      'customer_name': customerName,
      'customer_phone_masked': customerPhoneMasked,
      'wilaya': wilaya,
      'commune': commune,
      'delivery_address': deliveryAddress,
      'customer_notes': customerNotes,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

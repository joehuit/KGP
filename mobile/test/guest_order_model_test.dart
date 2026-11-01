import 'package:flutter_test/flutter_test.dart';
import 'package:kgp_list_mobile/models/guest_order.dart';

void main() {
  group('GuestOrder Models and Serialization', () {
    test('GuestOrderRequest serializes correctly to API JSON format', () {
      final request = GuestOrderRequest(
        fullName: 'Karim Belfort',
        phoneNumber: '0550123456',
        wilaya: '16 - Alger',
        commune: 'El Harrach',
        deliveryAddress: 'Rue de Belfort, Atelier 14',
        customerNotes: 'Appeler avant de livrer',
        items: [
          OrderItemRequest(productId: 10, quantity: 2),
          OrderItemRequest(productId: 15, quantity: 1),
        ],
      );

      final json = request.toJson();

      expect(json['full_name'], equals('Karim Belfort'));
      expect(json['phone_number'], equals('0550123456'));
      expect(json['wilaya'], equals('16 - Alger'));
      expect(json['commune'], equals('El Harrach'));
      expect(json['delivery_address'], equals('Rue de Belfort, Atelier 14'));
      expect(json['customer_notes'], equals('Appeler avant de livrer'));

      final items = json['items'] as List;
      expect(items.length, equals(2));
      expect(items[0]['product_id'], equals(10));
      expect(items[0]['quantity'], equals(2));
    });

    test('GuestOrderResponse deserializes correctly from backend response envelope data', () {
      final rawBackendData = {
        'id': 42,
        'order_reference': 'KGP-20261101-ABCD',
        'tracking_token': 'secret-guest-token-1234567890-abcdef',
        'status': 'PENDING',
        'total_amount': '17000.00',
        'customer_name': 'Karim Belfort',
        'customer_phone_masked': '0550****56',
        'wilaya': '16 - Alger',
        'commune': 'El Harrach',
        'delivery_address': 'Rue de Belfort',
        'customer_notes': 'Livraison urgente',
        'items': [
          {
            'id': 101,
            'order_id': 42,
            'product_id': 10,
            'product_name': 'Écran Samsung A52',
            'product_sku': 'SCR-SAM-A52',
            'unit_price': '8500.00',
            'quantity': 2,
            'total_price': '17000.00',
            'created_at': '2026-11-01T10:00:00Z',
          }
        ],
        'created_at': '2026-11-01T10:00:00Z',
      };

      final response = GuestOrderResponse.fromJson(rawBackendData);

      expect(response.id, equals(42));
      expect(response.orderReference, equals('KGP-20261101-ABCD'));
      expect(response.trackingToken, equals('secret-guest-token-1234567890-abcdef'));
      expect(response.status, equals('PENDING'));
      expect(response.totalAmount, equals(17000.00));
      expect(response.customerPhoneMasked, equals('0550****56'));
      expect(response.items.length, equals(1));
      expect(response.items[0].productName, equals('Écran Samsung A52'));
      expect(response.items[0].unitPrice, equals(8500.00));
      expect(response.localizedStatus, contains('قيد المراجعة'));
    });
  });
}

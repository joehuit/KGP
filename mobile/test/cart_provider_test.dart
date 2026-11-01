import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:kgp_list_mobile/models/product.dart';
import 'package:kgp_list_mobile/providers/cart_provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('CartProvider Unit Tests', () {
    late CartProvider cart;
    late Product sampleScreen;
    late Product sampleBattery;

    setUp(() {
      SharedPreferences.setMockInitialValues({});
      cart = CartProvider();

      sampleScreen = Product(
        id: 1,
        sku: 'SCR-SAM-A52',
        name: 'Écran OLED Samsung A52',
        categoryId: 1,
        sellingPrice: 8500.0,
        availableQuantity: 10,
        isActive: true,
      );

      sampleBattery = Product(
        id: 2,
        sku: 'BAT-IPH-12',
        name: 'Batterie iPhone 12',
        categoryId: 2,
        sellingPrice: 3800.0,
        availableQuantity: 5,
        isActive: true,
      );
    });

    test('initial cart is empty', () {
      expect(cart.isEmpty, isTrue);
      expect(cart.totalItemsCount, equals(0));
      expect(cart.totalAmount, equals(0.0));
    });

    test('addItem adds new product and computes total correctly', () {
      cart.addItem(sampleScreen, quantity: 2);

      expect(cart.isEmpty, isFalse);
      expect(cart.totalItemsCount, equals(2));
      expect(cart.totalAmount, equals(17000.0)); // 8500 * 2
      expect(cart.containsProduct(sampleScreen.id), isTrue);
      expect(cart.getQuantity(sampleScreen.id), equals(2));
    });

    test('addItem increments quantity if product already exists', () {
      cart.addItem(sampleScreen, quantity: 1);
      cart.addItem(sampleScreen, quantity: 2);

      expect(cart.items.length, equals(1));
      expect(cart.totalItemsCount, equals(3));
      expect(cart.totalAmount, equals(25500.0)); // 8500 * 3
    });

    test('updateQuantity modifies quantity or removes item on 0', () {
      cart.addItem(sampleScreen, quantity: 2);
      cart.updateQuantity(sampleScreen.id, 5);
      expect(cart.getQuantity(sampleScreen.id), equals(5));
      expect(cart.totalAmount, equals(42500.0));

      // Setting to 0 removes
      cart.updateQuantity(sampleScreen.id, 0);
      expect(cart.isEmpty, isTrue);
    });

    test('removeItem removes product completely', () {
      cart.addItem(sampleScreen, quantity: 2);
      cart.addItem(sampleBattery, quantity: 1);
      expect(cart.items.length, equals(2));

      cart.removeItem(sampleScreen.id);
      expect(cart.items.length, equals(1));
      expect(cart.containsProduct(sampleScreen.id), isFalse);
      expect(cart.containsProduct(sampleBattery.id), isTrue);
      expect(cart.totalAmount, equals(3800.0));
    });

    test('clear removes all items', () {
      cart.addItem(sampleScreen, quantity: 2);
      cart.addItem(sampleBattery, quantity: 3);
      expect(cart.isEmpty, isFalse);

      cart.clear();
      expect(cart.isEmpty, isTrue);
      expect(cart.totalItemsCount, equals(0));
      expect(cart.totalAmount, equals(0.0));
    });
  });
}

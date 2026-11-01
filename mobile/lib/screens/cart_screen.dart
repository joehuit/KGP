import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../core/utils/currency_formatter.dart';
import '../providers/cart_provider.dart';
import '../widgets/cart_item_tile.dart';
import '../widgets/empty_view.dart';
import 'guest_checkout_screen.dart';

/// Shopping cart screen showing current items, quantity adjustments, and total.
class CartScreen extends StatelessWidget {
  const CartScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('سلة المشتريات'),
        actions: [
          if (!cart.isEmpty)
            IconButton(
              icon: const Icon(Icons.delete_outline_rounded, color: AppTheme.error),
              tooltip: 'إفراغ السلة',
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    backgroundColor: AppTheme.getCardColor(context),
                    title: const Text('إفراغ السلة'),
                    content: const Text('هل أنت متأكد من حذف جميع القطع من السلة؟'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(ctx),
                        child: const Text('إلغاء'),
                      ),
                      TextButton(
                        onPressed: () {
                          cart.clear();
                          Navigator.pop(ctx);
                        },
                        child: const Text('نعم، إفراغ', style: TextStyle(color: AppTheme.error)),
                      ),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
      body: cart.isEmpty
          ? EmptyView(
              icon: Icons.remove_shopping_cart_outlined,
              title: 'سلة المشتريات فارغة',
              description: 'لم تقم بإضافة أي قطع غيار إلى سلتك بعد.\nتصفح الكتالوج واختر القطع المطلوبة لورشتك.',
              buttonText: 'تصفح قطع الغيار',
              onButtonPressed: () => Navigator.pop(context),
            )
          : Column(
              children: [
                // Cart Items List
                Expanded(
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: cart.items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final item = cart.items[index];
                      return CartItemTile(
                        item: item,
                        onQuantityChanged: (newQty) {
                          cart.updateQuantity(item.product.id, newQty);
                        },
                        onRemove: () {
                          cart.removeItem(item.product.id);
                        },
                      );
                    },
                  ),
                ),

                // Bottom Checkout Bar
                Container(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                  decoration: BoxDecoration(
                    color: AppTheme.getSurfaceColor(context),
                    border: Border(top: BorderSide(color: AppTheme.getBorderColor(context))),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Subtotal row
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'المجموع (${cart.totalItemsCount} قطعة):',
                            style: TextStyle(
                              fontSize: 14,
                              color: AppTheme.getTextSecondary(context),
                            ),
                          ),
                          Text(
                            CurrencyFormatter.format(cart.totalAmount),
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                              color: AppTheme.isDark(context)
                                  ? AppTheme.primaryLight
                                  : AppTheme.primary,
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 16),

                      // Checkout button
                      ElevatedButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const GuestCheckoutScreen(),
                            ),
                          );
                        },
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: const [
                            Icon(Icons.arrow_back_rounded, size: 20), // RTL back arrow is forward
                            SizedBox(width: 8),
                            Text('متابعة الطلب كزائر (بدون تسجيل)'),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}

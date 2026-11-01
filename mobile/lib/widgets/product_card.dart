import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../core/utils/currency_formatter.dart';
import '../models/product.dart';
import '../providers/cart_provider.dart';

/// Card widget representing an individual spare-part in the catalog grid.
class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback? onTap;

  const ProductCard({
    super.key,
    required this.product,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<CartProvider>(
      builder: (context, cart, child) {
        final inCart = cart.containsProduct(product.id);
        final cartQty = cart.getQuantity(product.id);

        return InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            decoration: BoxDecoration(
              color: AppTheme.getCardColor(context),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: inCart ? AppTheme.primary : AppTheme.getBorderColor(context),
                width: inCart ? 1.5 : 1.0,
              ),
              boxShadow: AppTheme.isDark(context)
                  ? []
                  : [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.04),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
            ),
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Top: Category tag & Stock Badge
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Stock badge
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: product.isInStock
                            ? AppTheme.success.withAlpha(AppTheme.isDark(context) ? 30 : 25)
                            : AppTheme.error.withAlpha(AppTheme.isDark(context) ? 30 : 25),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(
                          color: product.isInStock
                              ? AppTheme.success.withAlpha(75)
                              : AppTheme.error.withAlpha(75),
                        ),
                      ),
                      child: Text(
                        product.isInStock ? 'متوفر' : 'نفذ المخزون',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: product.isInStock ? AppTheme.success : AppTheme.error,
                        ),
                      ),
                    ),
                    // SKU chip
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppTheme.isDark(context)
                            ? Colors.black26
                            : Colors.black.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        product.sku,
                        style: TextStyle(
                          fontSize: 10,
                          color: AppTheme.getTextMuted(context),
                          fontFamily: 'monospace',
                        ),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 8),

                // Middle: Name
                Expanded(
                  child: Text(
                    product.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.getTextPrimary(context),
                      height: 1.3,
                    ),
                  ),
                ),

                const SizedBox(height: 8),

                // Bottom: Price & Add to Cart button
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    // Price
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          CurrencyFormatter.format(product.sellingPrice),
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.isDark(context)
                                ? AppTheme.primaryLight
                                : AppTheme.primary,
                          ),
                        ),
                      ],
                    ),

                    // Quick Cart Button
                    Material(
                      color: Colors.transparent,
                      child: InkWell(
                        onTap: product.isInStock
                            ? () {
                                cart.addItem(product, quantity: 1);
                                ScaffoldMessenger.of(context).hideCurrentSnackBar();
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text('تمت إضافة "${product.name}" إلى السلة'),
                                    duration: const Duration(seconds: 1),
                                    backgroundColor: AppTheme.primaryDark,
                                  ),
                                );
                              }
                            : null,
                        borderRadius: BorderRadius.circular(10),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: product.isInStock
                                ? (inCart
                                    ? AppTheme.primary
                                    : (AppTheme.isDark(context)
                                        ? AppTheme.getSurfaceColor(context)
                                        : AppTheme.primary.withOpacity(0.08)))
                                : AppTheme.getBorderColor(context).withAlpha(50),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: product.isInStock
                                  ? (inCart ? AppTheme.primary : AppTheme.primary)
                                  : AppTheme.getBorderColor(context),
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                inCart ? Icons.check : Icons.add_shopping_cart,
                                size: 14,
                                color: product.isInStock
                                    ? (inCart
                                        ? Colors.white
                                        : (AppTheme.isDark(context)
                                            ? Colors.white
                                            : AppTheme.primary))
                                    : AppTheme.getTextMuted(context),
                              ),
                              if (inCart) ...[
                                const SizedBox(width: 4),
                                const Text(
                                  '',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                                Text(
                                  '$cartQty',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

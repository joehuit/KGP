import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/app_constants.dart';
import '../core/theme/app_theme.dart';
import '../providers/cart_provider.dart';
import '../providers/catalog_provider.dart';
import '../widgets/category_chips.dart';
import '../widgets/empty_view.dart';
import '../widgets/error_view.dart';
import '../widgets/loading_view.dart';
import '../widgets/product_card.dart';
import 'cart_screen.dart';
import 'order_tracking_screen.dart';
import 'product_detail_screen.dart';

/// Main screen of KGP LIST Customer App showing spare-parts catalog, search, and categories.
class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final catalog = context.watch<CatalogProvider>();
    final cart = context.watch<CartProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppTheme.primary,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.build_rounded, size: 18, color: Colors.white),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  AppConstants.appName,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 0.5,
                  ),
                ),
                Text(
                  'بلفور — قطع الغيار الأصلية',
                  style: TextStyle(
                    fontSize: 10,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          // Order tracking shortcut
          IconButton(
            icon: const Icon(Icons.receipt_long_rounded),
            tooltip: 'متابعة الطلبات',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const OrderTrackingScreen()),
              );
            },
          ),
          // Shopping cart with live badge
          Stack(
            alignment: Alignment.center,
            children: [
              IconButton(
                icon: const Icon(Icons.shopping_cart_outlined),
                tooltip: 'سلة المشتريات',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const CartScreen()),
                  );
                },
              ),
              if (cart.totalItemsCount > 0)
                Positioned(
                  top: 8,
                  left: 8,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: const BoxDecoration(
                      color: AppTheme.primary,
                      shape: BoxShape.circle,
                    ),
                    constraints: const BoxConstraints(
                      minWidth: 18,
                      minHeight: 18,
                    ),
                    child: Text(
                      '${cart.totalItemsCount}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: catalog.refresh,
        color: AppTheme.primary,
        backgroundColor: AppTheme.surface,
        child: Column(
          children: [
            // Search Bar
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: TextField(
                controller: _searchController,
                textInputAction: TextInputAction.search,
                onSubmitted: (query) => catalog.search(query),
                onChanged: (val) {
                  if (val.isEmpty) catalog.search('');
                },
                decoration: InputDecoration(
                  hintText: 'ابحث برقم SKU أو اسم القطعة (مثال: OLED A51)...',
                  prefixIcon: const Icon(Icons.search, color: AppTheme.textMuted),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 18, color: AppTheme.textMuted),
                          onPressed: () {
                            _searchController.clear();
                            catalog.search('');
                          },
                        )
                      : null,
                ),
              ),
            ),

            // Category Chips
            if (catalog.categories.isNotEmpty) ...[
              const SizedBox(height: 4),
              CategoryChips(
                categories: catalog.categories,
                selectedCategoryId: catalog.selectedCategoryId,
                onSelected: (catId) => catalog.selectCategory(catId),
              ),
              const SizedBox(height: 8),
            ],

            // Products Grid / Status States
            Expanded(
              child: Builder(
                builder: (context) {
                  if (catalog.isLoading && catalog.products.isEmpty) {
                    return const LoadingView(message: 'جاري تحميل كتالوج قطع الغيار...');
                  }

                  if (catalog.hasError && catalog.products.isEmpty) {
                    return ErrorView(
                      message: catalog.errorMessage ?? 'تعذر الاتصال بخادم KGP LIST',
                      onRetry: catalog.refresh,
                    );
                  }

                  if (catalog.products.isEmpty) {
                    return EmptyView(
                      icon: Icons.search_off_rounded,
                      title: 'لم يتم العثور على قطع غيار',
                      description: 'لا توجد قطع مطابقة لبحثك في المخزون حالياً.',
                      buttonText: 'عرض جميع الفئات',
                      onButtonPressed: () {
                        _searchController.clear();
                        catalog.selectCategory(null);
                        catalog.search('');
                      },
                    );
                  }

                  return GridView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 0.72,
                    ),
                    itemCount: catalog.products.length,
                    itemBuilder: (context, index) {
                      final product = catalog.products[index];
                      return ProductCard(
                        product: product,
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => ProductDetailScreen(product: product),
                            ),
                          );
                        },
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/app_constants.dart';
import '../core/theme/app_theme.dart';
import '../providers/cart_provider.dart';
import '../providers/catalog_provider.dart';
import '../providers/theme_provider.dart';
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

  void _showThemeBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        final currentMode = context.watch<ThemeProvider>().themeMode;
        return Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppTheme.getBorderColor(ctx),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'اختيار مظهر التطبيق (Thème)',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.getTextPrimary(ctx),
                ),
              ),
              const SizedBox(height: 16),
              _buildThemeOption(
                context: ctx,
                title: 'المظهر الفاتح (Light Mode)',
                subtitle: 'خلفية بيضاء وبطاقات فاتحة ونصوص داكنة',
                icon: Icons.light_mode_rounded,
                selected: currentMode == ThemeMode.light,
                onTap: () {
                  context.read<ThemeProvider>().setThemeMode(ThemeMode.light);
                  Navigator.pop(ctx);
                },
              ),
              const SizedBox(height: 8),
              _buildThemeOption(
                context: ctx,
                title: 'المظهر الداكن (Dark Mode)',
                subtitle: 'المظهر الليلي المريح للعينين',
                icon: Icons.dark_mode_rounded,
                selected: currentMode == ThemeMode.dark,
                onTap: () {
                  context.read<ThemeProvider>().setThemeMode(ThemeMode.dark);
                  Navigator.pop(ctx);
                },
              ),
              const SizedBox(height: 8),
              _buildThemeOption(
                context: ctx,
                title: 'تلقائي حسب النظام (System Mode)',
                subtitle: 'يتوافق تلقائياً مع إعدادات جهازك',
                icon: Icons.brightness_auto_rounded,
                selected: currentMode == ThemeMode.system,
                onTap: () {
                  context.read<ThemeProvider>().setThemeMode(ThemeMode.system);
                  Navigator.pop(ctx);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildThemeOption({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: selected
              ? AppTheme.primary.withOpacity(0.12)
              : AppTheme.getCardColor(context),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? AppTheme.primary : AppTheme.getBorderColor(context),
            width: selected ? 1.5 : 1.0,
          ),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: selected
                  ? AppTheme.primary
                  : AppTheme.getTextSecondary(context),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: selected ? FontWeight.bold : FontWeight.w500,
                      color: AppTheme.getTextPrimary(context),
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontSize: 11,
                      color: AppTheme.getTextSecondary(context),
                    ),
                  ),
                ],
              ),
            ),
            if (selected)
              const Icon(
                Icons.check_circle_rounded,
                color: AppTheme.primary,
                size: 20,
              ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final catalog = context.watch<CatalogProvider>();
    final cart = context.watch<CartProvider>();
    final themeProvider = context.watch<ThemeProvider>();

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
              children: [
                const Text(
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
                    color: AppTheme.getTextSecondary(context),
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          // Theme mode selector
          IconButton(
            icon: Icon(
              themeProvider.themeMode == ThemeMode.light
                  ? Icons.light_mode_rounded
                  : themeProvider.themeMode == ThemeMode.dark
                      ? Icons.dark_mode_rounded
                      : Icons.brightness_auto_rounded,
            ),
            tooltip: 'مظهر التطبيق',
            onPressed: () => _showThemeBottomSheet(context),
          ),
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
        backgroundColor: AppTheme.getSurfaceColor(context),
        child: Column(
          children: [
            // Search Bar
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: TextField(
                controller: _searchController,
                textInputAction: TextInputAction.search,
                onSubmitted: (value) => catalog.search(value),
                decoration: InputDecoration(
                  hintText: 'ابحث عن شاشة، بطارية، أو كود SKU...',
                  prefixIcon: const Icon(Icons.search, size: 20),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 18),
                          onPressed: () {
                            _searchController.clear();
                            catalog.search('');
                            setState(() {});
                          },
                        )
                      : null,
                ),
                onChanged: (val) {
                  setState(() {});
                  if (val.isEmpty) {
                    catalog.search('');
                  }
                },
              ),
            ),

            // Categories horizontal list
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: CategoryChips(
                categories: catalog.categories,
                selectedCategoryId: catalog.selectedCategoryId,
                onSelected: (id) => catalog.selectCategory(id),
              ),
            ),

            const SizedBox(height: 4),

            // Products Grid / States
            Expanded(
              child: Builder(
                builder: (context) {
                  if (catalog.isLoading && catalog.products.isEmpty) {
                    return const LoadingView(message: 'جاري تحميل الكتالوج...');
                  }

                  if (catalog.errorMessage != null && catalog.products.isEmpty) {
                    return ErrorView(
                      message: catalog.errorMessage!,
                      onRetry: catalog.refresh,
                    );
                  }

                  if (catalog.products.isEmpty) {
                    return EmptyView(
                      title: 'لا توجد قطع غيار مطابقة',
                      message: 'جرب البحث بكلمات أخرى أو اختر فئة مختلفة.',
                      onAction: () {
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

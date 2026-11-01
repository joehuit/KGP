import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../core/theme/app_theme.dart';
import '../core/utils/currency_formatter.dart';
import '../models/guest_order.dart';
import 'order_tracking_screen.dart';

/// Screen displayed immediately after guest order submission showing reference and tracking options.
class OrderConfirmationScreen extends StatelessWidget {
  final GuestOrderResponse order;

  const OrderConfirmationScreen({super.key, required this.order});

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) {
          Navigator.of(context).popUntil((route) => route.isFirst);
        }
      },
      child: Scaffold(
        appBar: AppBar(
          automaticallyImplyLeading: false,
          title: const Text('تأكيد الطلب'),
          actions: [
            IconButton(
              icon: const Icon(Icons.close),
              tooltip: 'العودة للرئيسية',
              onPressed: () {
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
            ),
          ],
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Success Icon Animation / Graphic
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: AppTheme.primary.withAlpha(30),
                  shape: BoxShape.circle,
                  border: Border.all(color: AppTheme.primary, width: 2),
                ),
                child: const Icon(
                  Icons.check_rounded,
                  size: 44,
                  color: AppTheme.primaryLight,
                ),
              ),

              const SizedBox(height: 16),

              const Text(
                'تم تسجيل طلبك بنجاح!',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),

              const SizedBox(height: 6),

              const Text(
                'سيتصل بك فريق مبيعات KGP بلفور لتأكيد الإرسال والتحضير',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 13,
                  color: AppTheme.textSecondary,
                ),
              ),

              const SizedBox(height: 24),

              // Order Reference Box
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.cardSurface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.primaryLight.withAlpha(100)),
                ),
                child: Column(
                  children: [
                    const Text(
                      'رقم مرجع الطلب (Référence)',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          order.orderReference,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w900,
                            fontFamily: 'monospace',
                            color: AppTheme.primaryLight,
                            letterSpacing: 1.0,
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton(
                          icon: const Icon(Icons.copy_rounded, size: 18),
                          tooltip: 'نسخ المرجع',
                          onPressed: () {
                            Clipboard.setData(ClipboardData(text: order.orderReference));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('تم نسخ رقم المرجع إلى الحافظة'),
                                duration: Duration(seconds: 1),
                              ),
                            );
                          },
                        ),
                      ],
                    ),
                    const Divider(height: 20, color: AppTheme.border),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'حالة الطلب الأولية:',
                          style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppTheme.warning.withAlpha(25),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppTheme.warning.withAlpha(75)),
                          ),
                          child: Text(
                            order.localizedStatus,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.warning,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // Delivery details summary
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.cardSurface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'وجهة التوصيل',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'العميل: ${order.customerName}',
                      style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'الهاتف: ${order.customerPhoneMasked}',
                      style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'المنطقة: ${order.wilaya} — ${order.commune}',
                      style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'العنوان: ${order.deliveryAddress}',
                      style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                    ),
                    const Divider(height: 20, color: AppTheme.border),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'المبلغ الإجمالي:',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        Text(
                          CurrencyFormatter.format(order.totalAmount),
                          style: const TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.primaryLight,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 28),

              // Track Order Button
              ElevatedButton.icon(
                icon: const Icon(Icons.location_searching_rounded, size: 20),
                label: const Text('متابعة حالة الطلب مباشرة'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.cardSurface,
                  foregroundColor: AppTheme.textPrimary,
                  side: const BorderSide(color: AppTheme.primaryLight),
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => OrderTrackingScreen(
                        initialTrackingToken: order.trackingToken,
                      ),
                    ),
                  );
                },
              ),

              const SizedBox(height: 12),

              // Back to Catalog Button
              ElevatedButton.icon(
                icon: const Icon(Icons.storefront_rounded, size: 20),
                label: const Text('العودة إلى كتالوج قطع الغيار'),
                onPressed: () {
                  Navigator.of(context).popUntil((route) => route.isFirst);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

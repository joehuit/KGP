import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../core/utils/currency_formatter.dart';
import '../models/guest_order.dart';
import '../providers/order_provider.dart';
import '../widgets/empty_view.dart';
import '../widgets/error_view.dart';
import '../widgets/loading_view.dart';

/// Screen allowing guests to track order status using secure tracking token or recent local history.
class OrderTrackingScreen extends StatefulWidget {
  final String? initialTrackingToken;

  const OrderTrackingScreen({super.key, this.initialTrackingToken});

  @override
  State<OrderTrackingScreen> createState() => _OrderTrackingScreenState();
}

class _OrderTrackingScreenState extends State<OrderTrackingScreen> {
  final TextEditingController _tokenController = TextEditingController();

  bool _isLoading = false;
  String? _errorMessage;
  GuestOrderResponse? _trackedOrder;

  @override
  void initState() {
    super.initState();
    if (widget.initialTrackingToken != null && widget.initialTrackingToken!.isNotEmpty) {
      _tokenController.text = widget.initialTrackingToken!;
      _track(widget.initialTrackingToken!);
    }
  }

  @override
  void dispose() {
    _tokenController.dispose();
    super.dispose();
  }

  Future<void> _track(String token) async {
    final cleanToken = token.trim();
    if (cleanToken.isEmpty) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final orderProvider = context.read<OrderProvider>();
      final result = await orderProvider.trackOrder(cleanToken);
      setState(() {
        _trackedOrder = result;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _trackedOrder = null;
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return AppTheme.warning;
      case 'CONFIRMED':
      case 'PROCESSING':
        return AppTheme.accent;
      case 'SHIPPED':
        return Colors.blue;
      case 'DELIVERED':
        return AppTheme.success;
      case 'CANCELLED':
        return AppTheme.error;
      default:
        return AppTheme.textSecondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final orderProvider = context.watch<OrderProvider>();
    final savedOrders = orderProvider.savedOrders;

    return Scaffold(
      appBar: AppBar(
        title: const Text('متابعة حالة الطلب'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Tracking input box
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.getCardColor(context),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.getBorderColor(context)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'أدخل رمز تتبع الطلب (Code de suivi)',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.getTextPrimary(context),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _tokenController,
                          decoration: const InputDecoration(
                            hintText: 'رمز التتبع...',
                            prefixIcon: Icon(Icons.qr_code_scanner, color: AppTheme.textMuted),
                          ),
                          onSubmitted: _track,
                        ),
                      ),
                      const SizedBox(width: 10),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          minimumSize: const Size(80, 48),
                        ),
                        onPressed: () => _track(_tokenController.text),
                        child: const Text('تتبع'),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Tracked order result or recent orders list
            if (_isLoading) ...[
              const SizedBox(height: 40),
              const LoadingView(message: 'جاري جلب تفاصيل الطلب من خادم KGP...'),
            ] else if (_errorMessage != null) ...[
              const SizedBox(height: 20),
              ErrorView(
                message: _errorMessage!,
                onRetry: () => _track(_tokenController.text),
              ),
            ] else if (_trackedOrder != null) ...[
              _buildTrackedOrderCard(_trackedOrder!),
            ] else ...[
              // Recent orders stored on device
              if (savedOrders.isNotEmpty) ...[
                Text(
                  'طلباتك السابقة على هذا الهاتف',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.getTextPrimary(context),
                  ),
                ),
                const SizedBox(height: 12),
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: savedOrders.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final item = savedOrders[index];
                    final ref = item['order_reference'] as String? ?? '';
                    final token = item['tracking_token'] as String? ?? '';
                    final total = (item['total_amount'] as num?)?.toDouble() ?? 0.0;
                    final status = item['status'] as String? ?? 'PENDING';

                    return InkWell(
                      borderRadius: BorderRadius.circular(12),
                      onTap: () {
                        _tokenController.text = token;
                        _track(token);
                      },
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppTheme.getCardColor(context),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppTheme.getBorderColor(context)),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  ref,
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                    fontFamily: 'monospace',
                                    color: AppTheme.isDark(context)
                                        ? AppTheme.primaryLight
                                        : AppTheme.primary,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  CurrencyFormatter.format(total),
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: AppTheme.getTextSecondary(context),
                                  ),
                                ),
                              ],
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: _getStatusColor(status).withAlpha(25),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: _getStatusColor(status).withAlpha(75),
                                ),
                              ),
                              child: Text(
                                status,
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: _getStatusColor(status),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ] else ...[
                const SizedBox(height: 30),
                const EmptyView(
                  icon: Icons.history_rounded,
                  title: 'لا توجد طلبات محفوظة',
                  description: 'عند قيامك بطلب قطع غيار، سيتم حفظ رقم المرجع ورمز التتبع هنا تلقائياً.',
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildTrackedOrderCard(GuestOrderResponse order) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.getCardColor(context),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.getBorderColor(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Order Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('مرجع الطلب:', style: TextStyle(fontSize: 11, color: AppTheme.getTextMuted(context))),
                  Text(
                    order.orderReference,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'monospace',
                      color: AppTheme.isDark(context) ? AppTheme.primaryLight : AppTheme.primary,
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: _getStatusColor(order.status).withAlpha(30),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _getStatusColor(order.status),
                  ),
                ),
                child: Text(
                  order.localizedStatus,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: _getStatusColor(order.status),
                  ),
                ),
              ),
            ],
          ),

          Divider(height: 24, color: AppTheme.getBorderColor(context)),

          // Items Snapshot
          Text(
            'القطع المطلوبة:',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppTheme.getTextPrimary(context),
            ),
          ),
          const SizedBox(height: 8),

          ...order.items.map((it) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      '${it.quantity}x ${it.productName}',
                      style: TextStyle(fontSize: 12, color: AppTheme.getTextSecondary(context)),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Text(
                    CurrencyFormatter.format(it.totalPrice),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.getTextPrimary(context),
                    ),
                  ),
                ],
              ),
            );
          }),

          Divider(height: 24, color: AppTheme.getBorderColor(context)),

          // Destination
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('الوجهة:', style: TextStyle(fontSize: 12, color: AppTheme.getTextMuted(context))),
              Text(
                '${order.wilaya} — ${order.commune}',
                style: TextStyle(fontSize: 12, color: AppTheme.getTextSecondary(context)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('الهاتف:', style: TextStyle(fontSize: 12, color: AppTheme.getTextMuted(context))),
              Text(
                order.customerPhoneMasked,
                style: TextStyle(fontSize: 12, color: AppTheme.getTextSecondary(context)),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'المجموع الكلي:',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.getTextPrimary(context),
                ),
              ),
              Text(
                CurrencyFormatter.format(order.totalAmount),
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w900,
                  color: AppTheme.isDark(context) ? AppTheme.primaryLight : AppTheme.primary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

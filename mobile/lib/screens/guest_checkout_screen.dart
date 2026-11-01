import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../core/constants/app_constants.dart';
import '../core/theme/app_theme.dart';
import '../core/utils/currency_formatter.dart';
import '../core/utils/phone_validator.dart';
import '../models/guest_order.dart';
import '../providers/cart_provider.dart';
import '../providers/order_provider.dart';
import 'order_confirmation_screen.dart';

/// Frictionless Guest Checkout screen requiring zero login, zero password, zero OTP.
class GuestCheckoutScreen extends StatefulWidget {
  const GuestCheckoutScreen({super.key});

  @override
  State<GuestCheckoutScreen> createState() => _GuestCheckoutScreenState();
}

class _GuestCheckoutScreenState extends State<GuestCheckoutScreen> {
  final _formKey = GlobalKey<FormState>();

  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _communeController = TextEditingController();
  final TextEditingController _addressController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();

  String _selectedWilaya = AppConstants.algerianWilayas[15]; // Default: 16 - Alger
  late String _checkoutIdempotencyKey;

  @override
  void initState() {
    super.initState();
    _checkoutIdempotencyKey = const Uuid().v4();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _communeController.dispose();
    _addressController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _submitOrder() async {
    if (!_formKey.currentState!.validate()) return;

    final cart = context.read<CartProvider>();
    final orderProvider = context.read<OrderProvider>();

    if (cart.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('السلة فارغة. يرجى إضافة قطع غيار قبل إتمام الطلب.'),
          backgroundColor: AppTheme.error,
        ),
      );
      return;
    }

    final normalizedPhone = PhoneValidator.normalize(_phoneController.text.trim())!;

    final request = GuestOrderRequest(
      fullName: _nameController.text.trim(),
      phoneNumber: normalizedPhone,
      wilaya: _selectedWilaya,
      commune: _communeController.text.trim(),
      deliveryAddress: _addressController.text.trim(),
      customerNotes: _notesController.text.trim(),
      items: cart.items
          .map((item) => OrderItemRequest(
                productId: item.product.id,
                quantity: item.quantity,
              ))
          .toList(),
    );

    // Pass session idempotency key so retries due to network failure do not create duplicate orders
    final response = await orderProvider.submitGuestOrder(
      request,
      cart,
      idempotencyKey: _checkoutIdempotencyKey,
    );

    if (!mounted) return;

    if (response != null) {
      // Order placed successfully! Reset idempotency key for future checkouts
      _checkoutIdempotencyKey = const Uuid().v4();

      // Navigate to confirmation screen replacing checkout
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => OrderConfirmationScreen(order: response),
        ),
      );
    } else {
      // Show error banner
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(orderProvider.submitError ?? 'تعذر تأكيد الطلب. يرجى المحاولة ثانية.'),
          backgroundColor: AppTheme.error,
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartProvider>();
    final orderProvider = context.watch<OrderProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('إتمام الطلب (طلب سريع)'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Guest notice banner
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withAlpha(25),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.primary.withAlpha(75)),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.flash_on_rounded, color: AppTheme.primaryLight, size: 24),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'طلب مباشر وسريع بدون إنشاء حساب أو كلمة سر. أدخل معلومات التوصيل فقط.',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppTheme.textPrimary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Section: Contact & Delivery Info
              const Text(
                'معلومات الاتصال والتوصيل',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 16),

              // 1. Full Name
              TextFormField(
                controller: _nameController,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: 'الاسم الكامل أو اسم الورشة *',
                  hintText: 'مثال: كريم بلفور أو ورشة إلكترونيك بلفور',
                  prefixIcon: Icon(Icons.person_outline_rounded, color: AppTheme.textMuted),
                ),
                validator: (val) {
                  if (val == null || val.trim().length < 2) {
                    return 'يرجى إدخال اسم صحيح (حرفين على الأقل)';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // 2. Phone Number
              TextFormField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: 'رقم الهاتف الجزائري *',
                  hintText: '05XXXXXXXX أو 06XXXXXXXX أو 07XXXXXXXX',
                  prefixIcon: Icon(Icons.phone_android_rounded, color: AppTheme.textMuted),
                ),
                validator: (val) {
                  if (val == null || val.trim().isEmpty) {
                    return 'رقم الهاتف مطلوب لتأكيد التوصيل';
                  }
                  if (!PhoneValidator.isValid(val)) {
                    return 'رقم هاتف غير صالح. يجب أن يبدأ بـ 05 أو 06 أو 07 متبوعاً بـ 8 أرقام.';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // 3. Wilaya Dropdown
              DropdownButtonFormField<String>(
                value: _selectedWilaya,
                isExpanded: true,
                dropdownColor: AppTheme.cardSurface,
                decoration: const InputDecoration(
                  labelText: 'الولاية *',
                  prefixIcon: Icon(Icons.location_city_rounded, color: AppTheme.textMuted),
                ),
                items: AppConstants.algerianWilayas.map((wilaya) {
                  return DropdownMenuItem<String>(
                    value: wilaya,
                    child: Text(wilaya, style: const TextStyle(fontSize: 13)),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null) {
                    setState(() => _selectedWilaya = val);
                  }
                },
              ),

              const SizedBox(height: 16),

              // 4. Commune
              TextFormField(
                controller: _communeController,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: 'البلدية أو الحي *',
                  hintText: 'مثال: الحراش، بلفور، باب الزوار، بئر خادم...',
                  prefixIcon: Icon(Icons.map_outlined, color: AppTheme.textMuted),
                ),
                validator: (val) {
                  if (val == null || val.trim().length < 2) {
                    return 'يرجى إدخال اسم البلدية أو المنطقة';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // 5. Detailed Delivery Address
              TextFormField(
                controller: _addressController,
                textInputAction: TextInputAction.next,
                maxLines: 2,
                decoration: const InputDecoration(
                  labelText: 'العنوان الدقيق لمحل أو ورشة الصيانة *',
                  hintText: 'مثال: شارع بلفور التجاري، عمارة 4، مقابل صيدلية الرحمة...',
                  prefixIcon: Icon(Icons.storefront_rounded, color: AppTheme.textMuted),
                ),
                validator: (val) {
                  if (val == null || val.trim().length < 3) {
                    return 'يرجى إدخال عنوان دقيق للتسليم';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // 6. Optional Note
              TextFormField(
                controller: _notesController,
                textInputAction: TextInputAction.done,
                maxLines: 2,
                decoration: const InputDecoration(
                  labelText: 'ملاحظات إضافية للتوصيل (اختياري)',
                  hintText: 'مثال: الاتصال قبل نصف ساعة من الوصول، التسليم في الفترة الصباحية...',
                  prefixIcon: Icon(Icons.edit_note_rounded, color: AppTheme.textMuted),
                ),
              ),

              const SizedBox(height: 24),

              // Order Summary Box
              Container(
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
                      'ملخص الطلب',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'عدد القطع المطلوبة:',
                          style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                        ),
                        Text(
                          '${cart.totalItemsCount} قطع',
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: const [
                        Text(
                          'طريقة الدفع:',
                          style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
                        ),
                        Text(
                          'نقداً عند الاستلام (Main à main)',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryLight,
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 20, color: AppTheme.border),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'المجموع الكلي:',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        Text(
                          CurrencyFormatter.format(cart.totalAmount),
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.primaryLight,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Submit Button
              ElevatedButton(
                onPressed: orderProvider.isSubmitting ? null : _submitOrder,
                child: orderProvider.isSubmitting
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.check_circle_outline, size: 20),
                          SizedBox(width: 8),
                          Text('تأكيد الطلب الآن (Confirmer la commande)'),
                        ],
                      ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}

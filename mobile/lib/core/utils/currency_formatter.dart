import 'package:intl/intl.dart';
import '../constants/app_constants.dart';

/// Formatter for displaying prices accurately in Algerian Dinars (DZD).
class CurrencyFormatter {
  static final NumberFormat _formatter = NumberFormat('#,##0.00', 'fr_DZ');
  static final NumberFormat _compactFormatter = NumberFormat('#,##0', 'fr_DZ');

  /// Format decimal amount to Algerian Dinar string with currency symbol.
  /// Example: 8500.00 -> "8 500,00 د.ج"
  static String format(double amount, {bool showDecimals = true}) {
    final formattedNum = showDecimals ? _formatter.format(amount) : _compactFormatter.format(amount);
    return '$formattedNum ${AppConstants.currency}';
  }

  /// Format from double or num safely
  static String formatNum(num amount, {bool showDecimals = true}) {
    return format(amount.toDouble(), showDecimals: showDecimals);
  }
}

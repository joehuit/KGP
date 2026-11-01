/// Algerian mobile phone number validation and normalization utility.
class PhoneValidator {
  // Matches +213, 00213, or leading 0, followed by 5, 6, or 7 and 8 digits
  static final RegExp _algerianMobileRegex = RegExp(
    r'^(?:\+213|00213|0)([5-7][0-9]{8})$',
  );

  /// Validates whether the given string is a valid Algerian mobile number.
  static bool isValid(String? phone) {
    if (phone == null) return false;
    final cleaned = phone.replaceAll(RegExp(r'[\s\-\.]'), '');
    return _algerianMobileRegex.hasMatch(cleaned);
  }

  /// Normalizes phone number to standard national format (e.g. 0555123456).
  static String? normalize(String? phone) {
    if (phone == null) return null;
    final cleaned = phone.replaceAll(RegExp(r'[\s\-\.]'), '');
    final match = _algerianMobileRegex.firstMatch(cleaned);
    if (match != null && match.groupCount >= 1) {
      return '0${match.group(1)}';
    }
    return null;
  }

  /// Formats phone number for clean readable display: 0555 12 34 56
  static String formatForDisplay(String phone) {
    final norm = normalize(phone) ?? phone;
    if (norm.length == 10) {
      return '${norm.substring(0, 4)} ${norm.substring(4, 6)} ${norm.substring(6, 8)} ${norm.substring(8, 10)}';
    }
    return phone;
  }
}

import 'package:flutter_test/flutter_test.dart';
import 'package:kgp_list_mobile/core/utils/phone_validator.dart';

void main() {
  group('PhoneValidator (Algerian Mobile)', () {
    test('accepts valid 10-digit Ooredoo, Mobilis, and Djezzy numbers', () {
      expect(PhoneValidator.isValid('0550123456'), isTrue); // Ooredoo
      expect(PhoneValidator.isValid('0661223344'), isTrue); // Mobilis
      expect(PhoneValidator.isValid('0770998877'), isTrue); // Djezzy
    });

    test('accepts valid numbers with international prefixes and spaces', () {
      expect(PhoneValidator.isValid('+213 550 12 34 56'), isTrue);
      expect(PhoneValidator.isValid('00213 661-22-33-44'), isTrue);
      expect(PhoneValidator.isValid('+213770998877'), isTrue);
    });

    test('normalizes phone number to standard 0XXXXXXXXX format', () {
      expect(PhoneValidator.normalize('+213 550 12 34 56'), equals('0550123456'));
      expect(PhoneValidator.normalize('00213661223344'), equals('0661223344'));
      expect(PhoneValidator.normalize('0770-99-88-77'), equals('0770998877'));
    });

    test('rejects invalid Algerian numbers or landlines', () {
      expect(PhoneValidator.isValid('021554433'), isFalse); // Landline (021 Alger)
      expect(PhoneValidator.isValid('023112233'), isFalse); // Landline (023)
      expect(PhoneValidator.isValid('1234567890'), isFalse); // Missing mobile prefix
      expect(PhoneValidator.isValid('055012345'), isFalse); // Too short (9 digits)
      expect(PhoneValidator.isValid('05501234567'), isFalse); // Too long (11 digits)
      expect(PhoneValidator.isValid('abcdefghij'), isFalse);
      expect(PhoneValidator.isValid(''), isFalse);
      expect(PhoneValidator.isValid(null), isFalse);
    });
  });
}

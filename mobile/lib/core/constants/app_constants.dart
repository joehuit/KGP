/// Application constants for KGP LIST Mobile App.
class AppConstants {
  static const String appName = 'KGP LIST';
  static const String appSubtitle = 'قطع غيار الهواتف الذكية — بلفور';
  static const String currency = 'د.ج';
  static const String currencyCode = 'DZD';

  // Base API URL
  // Default to localhost/emulator. Can be overridden in production builds via --dart-define=API_URL=...
  static const String defaultApiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  // Local storage keys
  static const String cartStorageKey = 'kgp_cart_items_v1';
  static const String savedOrdersStorageKey = 'kgp_saved_guest_orders_v1';

  // All 58 Algerian Wilayas
  static const List<String> algerianWilayas = [
    '01 - أدرار (Adrar)',
    '02 - الشلف (Chlef)',
    '03 - الأغواط (Laghouat)',
    '04 - أم البواقي (Oum El Bouaghi)',
    '05 - باتنة (Batna)',
    '06 - بجاية (Béjaïa)',
    '07 - بسكرة (Biskra)',
    '08 - بشار (Béchar)',
    '09 - البليدة (Blida)',
    '10 - البويرة (Bouira)',
    '11 - تمنراست (Tamanrasset)',
    '12 - تبسة (Tébessa)',
    '13 - تلمسان (Tlemcen)',
    '14 - تيارت (Tiaret)',
    '15 - تيزي وزو (Tizi Ouzou)',
    '16 - الجزائر (Alger)',
    '17 - الجلفة (Djelfa)',
    '18 - جيجل (Jijel)',
    '19 - سطيف (Sétif)',
    '20 - سعيدة (Saïda)',
    '21 - سكيكدة (Skikda)',
    '22 - سيدي بلعباس (Sidi Bel Abbès)',
    '23 - عنابة (Annaba)',
    '24 - قالمة (Guelma)',
    '25 - قسنطينة (Constantine)',
    '26 - المدية (Médéa)',
    '27 - مستغانم (Mostaganem)',
    '28 - المسيلة (M\'Sila)',
    '29 - معسكر (Mascara)',
    '30 - ورقلة (Ouargla)',
    '31 - وهران (Oran)',
    '32 - البيض (El Bayadh)',
    '33 - إليزي (Illizi)',
    '34 - برج بوعريريج (Bordj Bou Arréridj)',
    '35 - بومرداس (Boumerdès)',
    '36 - الطارف (El Tarf)',
    '37 - تندوف (Tindouf)',
    '38 - تسمسيلت (Tissemsilt)',
    '39 - الوادي (El Oued)',
    '40 - خنشلة (Khenchela)',
    '41 - سوق أهراس (Souk Ahras)',
    '42 - تيبازة (Tipaza)',
    '43 - ميلة (Mila)',
    '44 - عين الدفلى (Aïn Defla)',
    '45 - النعامة (Naâma)',
    '46 - عين تموشنت (Aïn Témouchent)',
    '47 - غرداية (Ghardaïa)',
    '48 - غليزان (Relizane)',
    '49 - تيميمون (Timimoun)',
    '50 - برج باجي مختار (Bordj Badji Mokhtar)',
    '51 - أولاد جلال (Ouled Djellal)',
    '52 - بني عباس (Béni Abbès)',
    '53 - عين صالح (In Salah)',
    '54 - عين قزام (In Guezzam)',
    '55 - تقرت (Touggourt)',
    '56 - جانت (Djanet)',
    '57 - المغير (El M\'Ghair)',
    '58 - المنيعة (El Meniaa)',
  ];
}

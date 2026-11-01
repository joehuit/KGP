/// Product model representing an individual spare-part piece in the catalog.
class Product {
  final int id;
  final String sku;
  final String name;
  final int categoryId;
  final String? categoryName;
  final double sellingPrice;
  final int? availableQuantity;
  final String? description;
  final bool isActive;

  Product({
    required this.id,
    required this.sku,
    required this.name,
    required this.categoryId,
    this.categoryName,
    required this.sellingPrice,
    this.availableQuantity,
    this.description,
    this.isActive = true,
  });

  bool get isInStock => availableQuantity == null || availableQuantity! > 0;
  bool get isLowStock => availableQuantity != null && availableQuantity! > 0 && availableQuantity! <= 5;

  factory Product.fromJson(Map<String, dynamic> json) {
    double parsePrice(dynamic val) {
      if (val is num) return val.toDouble();
      if (val is String) return double.tryParse(val) ?? 0.0;
      return 0.0;
    }

    return Product(
      id: json['id'] as int,
      sku: json['sku'] as String,
      name: json['name'] as String,
      categoryId: json['category_id'] as int,
      categoryName: json['category_name'] as String?,
      sellingPrice: parsePrice(json['selling_price']),
      availableQuantity: json['available_quantity'] as int?,
      description: json['description'] as String?,
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'sku': sku,
      'name': name,
      'category_id': categoryId,
      'category_name': categoryName,
      'selling_price': sellingPrice,
      'available_quantity': availableQuantity,
      'description': description,
      'is_active': isActive,
    };
  }
}

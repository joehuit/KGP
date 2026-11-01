/// Category model representing a phone spare-part classification.
class Category {
  final int id;
  final String name;
  final int displayOrder;
  final bool isActive;

  Category({
    required this.id,
    required this.name,
    this.displayOrder = 0,
    this.isActive = true,
  });

  factory Category.fromJson(Map<String, dynamic> json) {
    return Category(
      id: json['id'] as int,
      name: json['name'] as String,
      displayOrder: json['display_order'] as int? ?? 0,
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'display_order': displayOrder,
      'is_active': isActive,
    };
  }
}

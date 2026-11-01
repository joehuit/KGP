import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../models/category.dart';

/// Horizontal scrollable chips for selecting spare-part categories.
class CategoryChips extends StatelessWidget {
  final List<Category> categories;
  final int? selectedCategoryId;
  final ValueChanged<int?> onSelected;

  const CategoryChips({
    super.key,
    required this.categories,
    required this.selectedCategoryId,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 42,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: categories.length + 1, // +1 for "All" (الكل)
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          if (index == 0) {
            final isSelected = selectedCategoryId == null;
            return ChoiceChip(
              label: const Text('جميع الفئات'),
              selected: isSelected,
              onSelected: (_) => onSelected(null),
              selectedColor: AppTheme.primary,
              backgroundColor: AppTheme.cardSurface,
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : AppTheme.textSecondary,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                fontSize: 12,
              ),
              side: BorderSide(
                color: isSelected ? AppTheme.primary : AppTheme.border,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
              ),
            );
          }

          final cat = categories[index - 1];
          final isSelected = selectedCategoryId == cat.id;

          return ChoiceChip(
            label: Text(cat.name),
            selected: isSelected,
            onSelected: (_) => onSelected(cat.id),
            selectedColor: AppTheme.primary,
            backgroundColor: AppTheme.cardSurface,
            labelStyle: TextStyle(
              color: isSelected ? Colors.white : AppTheme.textSecondary,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              fontSize: 12,
            ),
            side: BorderSide(
              color: isSelected ? AppTheme.primary : AppTheme.border,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
          );
        },
      ),
    );
  }
}

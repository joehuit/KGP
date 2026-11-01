import 'package:flutter/foundation.dart';
import '../models/category.dart';
import '../models/product.dart';
import '../services/api_service.dart';

/// Provider managing catalog products, dynamic categories, and search state.
class CatalogProvider extends ChangeNotifier {
  final ApiService apiService;

  List<Category> _categories = [];
  List<Product> _products = [];
  int? _selectedCategoryId;
  String _searchQuery = '';
  bool _isLoading = false;
  String? _errorMessage;

  CatalogProvider({required this.apiService}) {
    fetchInitialData();
  }

  List<Category> get categories => List.unmodifiable(_categories);
  List<Product> get products => List.unmodifiable(_products);
  int? get selectedCategoryId => _selectedCategoryId;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get hasError => _errorMessage != null;

  /// Fetch both categories and products on application startup.
  Future<void> fetchInitialData() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final results = await Future.wait([
        apiService.getCategories(),
        apiService.getProducts(categoryId: _selectedCategoryId, search: _searchQuery),
      ]);

      _categories = results[0] as List<Category>;
      _products = results[1] as List<Product>;
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Select a category filter (passing null selects "All" / جميع القطع).
  Future<void> selectCategory(int? categoryId) async {
    if (_selectedCategoryId == categoryId) return;
    _selectedCategoryId = categoryId;
    await _fetchProducts();
  }

  /// Perform text search across product names and SKUs.
  Future<void> search(String query) async {
    final trimmed = query.trim();
    if (_searchQuery == trimmed) return;
    _searchQuery = trimmed;
    await _fetchProducts();
  }

  /// Refresh products list with active filters.
  Future<void> _fetchProducts() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _products = await apiService.getProducts(
        categoryId: _selectedCategoryId,
        search: _searchQuery,
      );
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// User pull-to-refresh action.
  Future<void> refresh() async {
    await fetchInitialData();
  }
}

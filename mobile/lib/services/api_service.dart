import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';
import '../core/constants/app_constants.dart';
import '../models/category.dart';
import '../models/guest_order.dart';
import '../models/product.dart';

/// Exception thrown when an API request fails with server or network error.
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

/// Service handling all HTTP communication with KGP LIST FastAPI backend.
class ApiService {
  final String baseUrl;
  final http.Client client;

  ApiService({
    String? baseUrl,
    http.Client? client,
  })  : baseUrl = baseUrl ?? AppConstants.defaultApiUrl,
        client = client ?? http.Client();

  /// Parse response envelope: { "success": true, "data": ..., "message": ... }
  dynamic _parseResponse(http.Response response) {
    dynamic body;
    try {
      body = jsonDecode(utf8.decode(response.bodyBytes));
    } catch (_) {
      throw ApiException(
        'خطأ في معالجة استجابة الخادم (Format Error)',
        statusCode: response.statusCode,
      );
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (body is Map<String, dynamic> && body.containsKey('data')) {
        return body['data'];
      }
      return body;
    }

    // Extract error message from uniform envelope
    String errorMessage = 'حدث خطأ غير متوقع (${response.statusCode})';
    if (body is Map<String, dynamic>) {
      if (body.containsKey('error') && body['error'] is Map) {
        final err = body['error'] as Map<String, dynamic>;
        errorMessage = err['message'] as String? ?? errorMessage;
      } else if (body.containsKey('detail')) {
        final detail = body['detail'];
        if (detail is String) {
          errorMessage = detail;
        } else if (detail is Map && detail.containsKey('message')) {
          errorMessage = detail['message'] as String;
        }
      } else if (body.containsKey('message')) {
        errorMessage = body['message'] as String;
      }
    }

    throw ApiException(errorMessage, statusCode: response.statusCode);
  }

  /// Fetch list of active spare-parts categories.
  Future<List<Category>> getCategories() async {
    try {
      final uri = Uri.parse('$baseUrl/categories?active_only=true');
      final response = await client.get(
        uri,
        headers: {'Accept': 'application/json'},
      );
      final data = _parseResponse(response);

      if (data is List) {
        return data.map((json) => Category.fromJson(json as Map<String, dynamic>)).toList();
      }
      return [];
    } on SocketException {
      throw ApiException('تعذر الاتصال بالخادم. يرجى التحقق من اتصال الإنترنت.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('تعذر تحميل الفئات: $e');
    }
  }

  /// Fetch paginated spare-parts products with optional category and search filters.
  Future<List<Product>> getProducts({
    int? categoryId,
    String? search,
    int page = 1,
    int pageSize = 50,
  }) async {
    try {
      final queryParams = {
        'page': page.toString(),
        'page_size': pageSize.toString(),
        'active_only': 'true',
        if (categoryId != null) 'category_id': categoryId.toString(),
        if (search != null && search.trim().isNotEmpty) 'search': search.trim(),
      };

      final uri = Uri.parse('$baseUrl/products').replace(queryParameters: queryParams);
      final response = await client.get(
        uri,
        headers: {'Accept': 'application/json'},
      );
      final data = _parseResponse(response);

      if (data is Map<String, dynamic> && data.containsKey('items')) {
        final items = data['items'] as List<dynamic>;
        return items.map((json) => Product.fromJson(json as Map<String, dynamic>)).toList();
      }
      return [];
    } on SocketException {
      throw ApiException('تعذر الاتصال بالخادم. يرجى التحقق من اتصال الإنترنت.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('تعذر تحميل قطع الغيار: $e');
    }
  }

  /// Submit a frictionless guest checkout order (Zero OTP, zero login).
  Future<GuestOrderResponse> submitGuestOrder(
    GuestOrderRequest request, {
    String? idempotencyKey,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/orders/guest');
      final effectiveKey = idempotencyKey ?? const Uuid().v4();

      final response = await client.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Idempotency-Key': effectiveKey,
        },
        body: jsonEncode(request.toJson()),
      );

      final data = _parseResponse(response);
      return GuestOrderResponse.fromJson(data as Map<String, dynamic>);
    } on SocketException {
      throw ApiException('تعذر إرسال الطلب. يرجى التحقق من اتصال الإنترنت والمحاولة ثانية.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('تعذر تأكيد الطلب: $e');
    }
  }

  /// Track a guest order securely using POST body to prevent token leakage in URI logs.
  Future<GuestOrderResponse> trackGuestOrder(String trackingToken) async {
    try {
      final uri = Uri.parse('$baseUrl/orders/guest/track');
      final response = await client.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode({'tracking_token': trackingToken.trim()}),
      );
      final data = _parseResponse(response);
      return GuestOrderResponse.fromJson(data as Map<String, dynamic>);
    } on SocketException {
      throw ApiException('تعذر الاتصال بالخادم لمتابعة الطلب.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('تعذر العثور على الطلب: $e');
    }
  }
}

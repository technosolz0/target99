import 'package:dio/dio.dart';
import 'package:target99/core/constants/api_constants.dart';

class ApiClient {
  final Dio _dio;
  String? _token;

  ApiClient()
      : _dio = Dio(BaseOptions(
          baseUrl: ApiConstants.baseUrl,
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 15),
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_token != null) {
          options.headers['Authorization'] = 'Bearer $_token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        // Centralized error interceptor
        return handler.next(e);
      },
    ));
  }

  void setToken(String? token) {
    _token = token;
  }

  bool get hasToken => _token != null && _token!.isNotEmpty;

  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.get(path, queryParameters: queryParameters);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Response> post(String path, {dynamic data, Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.post(path, data: data, queryParameters: queryParameters);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(DioException error) {
    final response = error.response;
    if (response != null && response.data != null) {
      final data = response.data;
      if (data is Map && data.containsKey('detail')) {
        return Exception(data['detail'].toString());
      }
    }
    return Exception(error.message ?? 'An unknown connection error occurred');
  }
}

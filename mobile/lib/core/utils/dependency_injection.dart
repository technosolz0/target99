import 'package:get_it/get_it.dart';
import 'package:target99/core/network/api_client.dart';

final getIt = GetIt.instance;

void setupDependencyInjection() {
  // Register API Client as Singleton
  getIt.registerSingleton<ApiClient>(ApiClient());
}

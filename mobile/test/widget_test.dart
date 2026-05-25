import 'package:flutter_test/flutter_test.dart';
import 'package:target99/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const Target99App());
    expect(find.byType(Target99App), findsOneWidget);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:target99/core/theme/app_theme.dart';
import 'package:target99/core/utils/dependency_injection.dart';
import 'package:target99/core/network/api_client.dart';
import 'package:target99/features/app_bloc.dart';
import 'package:target99/features/auth/login_screen.dart';
import 'package:target99/features/home/home_screen.dart';
import 'package:target99/features/wallet/wallet_screen.dart';
import 'package:target99/features/referral/referral_screen.dart';
import 'package:target99/features/profile/profile_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Set up dependency injection container
  setupDependencyInjection();
  
  runApp(const Target99App());
}

class Target99App extends StatelessWidget {
  const Target99App({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider<AppBloc>(
      create: (context) => AppBloc(getIt<ApiClient>()),
      child: MaterialApp(
        title: 'target99',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        home: const AuthWrapper(),
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AppBloc, AppState>(
      builder: (context, state) {
        if (state.token != null && state.currentUser != null) {
          // Authenticated User
          return const MainNavigationLayout();
        }
        // Guest User
        return const LoginScreen();
      },
    );
  }
}

class MainNavigationLayout extends StatefulWidget {
  const MainNavigationLayout({super.key});

  @override
  State<MainNavigationLayout> createState() => _MainNavigationLayoutState();
}

class _MainNavigationLayoutState extends State<MainNavigationLayout> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    WalletScreen(),
    ReferralScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(
            top: BorderSide(color: AppTheme.borderCol, width: 1),
          ),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() {
              _currentIndex = index;
            });
            // Fetch updates contextually on tab switch
            if (index == 1) {
              context.read<AppBloc>().add(FetchTransactionsEvent());
            } else if (index == 2) {
              context.read<AppBloc>().add(FetchReferralDetailsEvent());
            } else if (index == 3) {
              context.read<AppBloc>().add(LoadProfileEvent());
            }
          },
          type: BottomNavigationBarType.fixed,
          backgroundColor: AppTheme.darkBg,
          selectedItemColor: AppTheme.accentCyan,
          unselectedItemColor: AppTheme.textMuted,
          selectedFontSize: 11,
          unselectedFontSize: 11,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.sports_esports_outlined),
              activeIcon: Icon(Icons.sports_esports),
              label: 'Lobbies',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.account_balance_wallet_outlined),
              activeIcon: Icon(Icons.account_balance_wallet),
              label: 'Wallet',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.card_giftcard_outlined),
              activeIcon: Icon(Icons.card_giftcard),
              label: 'Refer & Earn',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline),
              activeIcon: Icon(Icons.person),
              label: 'Profile',
            ),
          ],
        ),
      ),
    );
  }
}

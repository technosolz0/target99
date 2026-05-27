import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:target99/core/theme/app_theme.dart';
import 'package:target99/core/widgets/custom_button.dart';
import 'package:target99/core/widgets/custom_text_field.dart';
import 'package:target99/features/app_bloc.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  final _referralController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();

  bool _otpSent = false;

  @override
  void initState() {
    super.initState();
    FirebaseAnalytics.instance.logScreenView(screenName: 'RegisterScreen');
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    _referralController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BlocListener<AppBloc, AppState>(
        listener: (context, state) {
          if (state.otpSentMessage != null && !_otpSent) {
            setState(() {
              _otpSent = true;
            });
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.otpSentMessage!),
                backgroundColor: AppTheme.accentCyan,
              ),
            );
          }
          if (state.authError != null) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.authError!),
                backgroundColor: AppTheme.accentRed,
              ),
            );
          }
        },
        child: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [AppTheme.darkBg, Color(0xFF0F1426)],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
          child: SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Brand Logo
                    Center(
                      child: Column(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: LinearGradient(
                                colors: [
                                  AppTheme.accentCyan,
                                  AppTheme.accentPurple,
                                ],
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: AppTheme.accentCyan.withOpacity(0.3),
                                  blurRadius: 20,
                                  spreadRadius: 2,
                                ),
                              ],
                            ),
                            child: const Icon(
                              Icons.person_add_alt_1,
                              size: 48,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 16),
                          RichText(
                            text: const TextSpan(
                              style: TextStyle(
                                fontSize: 32,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -1,
                              ),
                              children: [
                                TextSpan(
                                  text: 'target',
                                  style: TextStyle(color: AppTheme.accentCyan),
                                ),
                                TextSpan(
                                  text: '99',
                                  style: TextStyle(color: Colors.white),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'CREATE A NEW ACCOUNT',
                            style: TextStyle(
                              fontSize: 10,
                              color: AppTheme.textMuted,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 2.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 48),

                    // Glass Card Container
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(24.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _otpSent ? 'Enter verification code' : 'Sign Up',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              _otpSent
                                  ? 'We sent a 6-digit OTP to your phone'
                                  : 'Enter details below to register',
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppTheme.textMuted,
                              ),
                            ),
                            const SizedBox(height: 24),

                             // First and Last Name Inputs
                            CustomTextField(
                              controller: _firstNameController,
                              labelText: 'First Name',
                              hintText: 'Enter your first name',
                              enabled: !_otpSent,
                              textCapitalization: TextCapitalization.words,
                              prefixIcon: const Icon(
                                Icons.person_outline,
                                size: 20,
                              ),
                            ),
                            const SizedBox(height: 16),

                            CustomTextField(
                              controller: _lastNameController,
                              labelText: 'Last Name',
                              hintText: 'Enter your last name',
                              enabled: !_otpSent,
                              textCapitalization: TextCapitalization.words,
                              prefixIcon: const Icon(
                                Icons.person_outline,
                                size: 20,
                              ),
                            ),
                            const SizedBox(height: 16),

                            // Phone Input
                            CustomTextField(
                              controller: _phoneController,
                              labelText: 'Phone Number',
                              hintText: 'Enter 10-digit number',
                              keyboardType: TextInputType.phone,
                              enabled: !_otpSent,
                              prefixIcon: const Icon(
                                Icons.phone_iphone,
                                size: 20,
                              ),
                            ),
                            const SizedBox(height: 16),

                            // Referral Input (optional)
                            if (!_otpSent) ...[
                              CustomTextField(
                                controller: _referralController,
                                labelText: 'Referral Code (Optional)',
                                hintText: 'e.g. T99_WXYZ',
                                textCapitalization: TextCapitalization.characters,
                                prefixIcon: const Icon(
                                  Icons.card_giftcard,
                                  size: 20,
                                ),
                              ),
                              const SizedBox(height: 24),
                            ],

                            // OTP input if sent
                            if (_otpSent) ...[
                              CustomTextField(
                                controller: _otpController,
                                labelText: '6-digit OTP',
                                hintText: 'Enter OTP',
                                keyboardType: TextInputType.number,
                                prefixIcon: const Icon(
                                  Icons.lock_outline,
                                  size: 20,
                                ),
                              ),
                              const SizedBox(height: 24),
                            ],

                             BlocBuilder<AppBloc, AppState>(
                              builder: (context, state) {
                                return CustomButton(
                                  text: _otpSent
                                      ? 'VERIFY & REGISTER'
                                      : 'GET VERIFICATION CODE',
                                  isLoading: state.isAuthLoading,
                                  onPressed: () {
                                    final firstName = _firstNameController.text.trim();
                                    final lastName = _lastNameController.text.trim();
                                    final phone = _phoneController.text.trim();

                                    if (firstName.isEmpty || lastName.isEmpty) {
                                      ScaffoldMessenger.of(context).showSnackBar(
                                        const SnackBar(
                                          content: Text('Please enter both your first and last name'),
                                          backgroundColor: AppTheme.accentPurple,
                                        ),
                                      );
                                      return;
                                    }

                                    if (phone.isEmpty || phone.length < 10) {
                                      ScaffoldMessenger.of(context).showSnackBar(
                                        const SnackBar(
                                          content: Text('Please enter a valid 10-digit phone number'),
                                          backgroundColor: AppTheme.accentPurple,
                                        ),
                                      );
                                      return;
                                    }

                                    if (!_otpSent) {
                                      context.read<AppBloc>().add(
                                        SendOtpEvent(phone, isRegister: true),
                                      );
                                    } else {
                                      final otp = _otpController.text.trim();
                                      final ref = _referralController.text.trim();
                                      if (otp.length < 6) {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(
                                            content: Text('Please enter a valid 6-digit OTP'),
                                            backgroundColor: AppTheme.accentPurple,
                                          ),
                                        );
                                        return;
                                      }

                                      context.read<AppBloc>().add(
                                        VerifyOtpEvent(
                                          phone,
                                          otp,
                                          referredBy: ref.isNotEmpty ? ref : null,
                                          firstName: firstName,
                                          lastName: lastName,
                                        ),
                                      );
                                    }
                                  },
                                );
                              },
                            ),

                            const SizedBox(height: 16),

                            // Switch screen links
                            if (!_otpSent) ...[
                              Center(
                                child: TextButton(
                                  onPressed: () {
                                    Navigator.pop(context);
                                  },
                                  child: RichText(
                                    text: const TextSpan(
                                      style: TextStyle(
                                        fontSize: 12,
                                        fontFamily: 'Inter',
                                      ),
                                      children: [
                                        TextSpan(
                                          text: "Already have an account? ",
                                          style: TextStyle(
                                            color: AppTheme.textMuted,
                                          ),
                                        ),
                                        TextSpan(
                                          text: 'Log In',
                                          style: TextStyle(
                                            color: AppTheme.accentCyan,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ] else ...[
                              Center(
                                child: TextButton(
                                  onPressed: () {
                                    setState(() {
                                      _otpSent = false;
                                      _otpController.clear();
                                    });
                                  },
                                  child: const Text(
                                    'Change registration details',
                                    style: TextStyle(
                                      color: AppTheme.accentCyan,
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),
                    const Center(
                      child: Text(
                        'By continuing, you agree that you are 18+ years of age.\nRestricted states include Assam, Odisha, Sikkim, Nagaland.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 10,
                          color: AppTheme.textMuted,
                          height: 1.5,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

/// Paper / charcoal surfaces with an Aziel gold accent.
/// Light and dark follow the system. No analytics.
const Color kNavy = Color(0xFF12110E);
const Color kSurface = Color(0xFF1C1A16);
const Color kGold = Color(0xFFC9A227);
const Color kPaper = Color(0xFFF7F4EE);
const Color kPaperCard = Color(0xFFFFFDF8);
const Color kInk = Color(0xFF1C1915);
const Color kTeal = Color(0xFF3D9B84);
const Color kIvory = Color(0xFFF3EFE6);
const Color kWarn = Color(0xFF8A6A10);

ThemeData buildAppTheme(Brightness brightness) {
  final dark = brightness == Brightness.dark;
  final scheme = ColorScheme(
    brightness: brightness,
    primary: kGold,
    onPrimary: kInk,
    secondary: kTeal,
    onSecondary: dark ? kIvory : Colors.white,
    surface: dark ? kSurface : kPaperCard,
    onSurface: dark ? kIvory : kInk,
    error: const Color(0xFF9A3030),
    onError: Colors.white,
  );
  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: scheme,
    scaffoldBackgroundColor: dark ? kNavy : kPaper,
    focusColor: kGold,
    splashColor: const Color(0x33C9A227),
    appBarTheme: AppBarTheme(
      backgroundColor: dark ? kNavy : kPaperCard,
      foregroundColor: dark ? kIvory : kInk,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: dark ? kSurface : kPaperCard,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: dark ? const Color(0x33C9A227) : const Color(0xFFE4DCCB)),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: dark ? kNavy : kPaperCard,
      indicatorColor: const Color(0x33C9A227),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      focusedBorder: OutlineInputBorder(
        borderSide: BorderSide(color: kGold, width: 2),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: kGold,
        foregroundColor: kInk,
      ),
    ),
  );
}

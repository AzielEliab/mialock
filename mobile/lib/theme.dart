import 'package:flutter/material.dart';

/// Dark navy + gold Material 3 theme stamped to the rose-star brand mark.
/// No analytics.
const Color kNavy = Color(0xFF0B1220);
const Color kSurface = Color(0xFF141C24);
const Color kGold = Color(0xFFC9A227);
const Color kGoldDim = Color(0xFF8A7219);
const Color kTeal = Color(0xFF3D9B84);
const Color kIvory = Color(0xFFE8E0D0);
const Color kWarn = Color(0xFFD4A574);

ThemeData buildAppTheme() {
  const scheme = ColorScheme.dark(
    brightness: Brightness.dark,
    primary: kGold,
    onPrimary: kNavy,
    secondary: kTeal,
    onSecondary: kIvory,
    surface: kSurface,
    onSurface: kIvory,
    error: Color(0xFFB54A4A),
    onError: kIvory,
  );
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: scheme,
    scaffoldBackgroundColor: kNavy,
    appBarTheme: const AppBarTheme(
      backgroundColor: kNavy,
      foregroundColor: kGold,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: kSurface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: Color(0x33C9A227)),
      ),
    ),
    navigationBarTheme: const NavigationBarThemeData(
      backgroundColor: kNavy,
      indicatorColor: Color(0x33C9A227),
    ),
  );
}

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Manages and persists the application's theme mode (Light, Dark, or System).
class ThemeProvider extends ChangeNotifier {
  static const String _storageKey = 'kgp_mobile_theme_mode';

  ThemeMode _themeMode = ThemeMode.system;

  ThemeMode get themeMode => _themeMode;

  ThemeProvider() {
    _loadThemeMode();
  }

  Future<void> _loadThemeMode() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString(_storageKey);
      if (saved == 'light') {
        _themeMode = ThemeMode.light;
      } else if (saved == 'dark') {
        _themeMode = ThemeMode.dark;
      } else {
        _themeMode = ThemeMode.system;
      }
      notifyListeners();
    } catch (_) {
      // In case SharedPreferences fails or is mock-initialized
    }
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    if (_themeMode == mode) return;
    _themeMode = mode;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      String val;
      switch (mode) {
        case ThemeMode.light:
          val = 'light';
          break;
        case ThemeMode.dark:
          val = 'dark';
          break;
        case ThemeMode.system:
        default:
          val = 'system';
          break;
      }
      await prefs.setString(_storageKey, val);
    } catch (_) {
      // Ignore
    }
  }
}

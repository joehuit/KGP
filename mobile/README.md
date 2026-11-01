# KGP LIST — Mobile Customer Application (Phase 4)
## Guest Checkout — No Mandatory Registration

The **KGP LIST Customer Application** is a native-performance mobile application built with **Flutter**, designed specifically for smartphone repair shop technicians, workshops, and retail buyers in Algeria (Belfort, El Harrach, and all 58 wilayas).

---

## 1. Core Architecture & Frictionless Ordering

To maximize ease of ordering and minimize friction, the application implements a strict **Guest Checkout policy**:
- **Zero Account Creation Required:** Technicians open the app directly to the spare-parts catalog.
- **Zero Passwords or OTP Verification:** Orders are placed with contact and delivery details only.
- **Persistent Local Cart:** Cart contents survive application restarts and category browsing via `shared_preferences`.
- **Server-Side Validation:** All prices, totals, and line snapshots are calculated securely on the backend server.
- **Secure Unguessable Tracking:** Order references and cryptographically unguessable tracking tokens are issued upon order placement, allowing live status tracking without exposing sensitive customer data.

---

## 2. Customer Journey

1. **Direct Catalog Browsing:** Browse screens, batteries, connectors, cameras, and ICs across dynamic categories loaded from `GET /api/v1/categories`.
2. **Instant Search:** Search across SKU codes (e.g. `OLED-A52`) and model designations.
3. **Product Inspection:** Check real-time stock availability, descriptions, and prices in Algerian Dinars (`د.ج`).
4. **Persistent Cart:** Add items, adjust quantities, and remove items with real-time total calculations.
5. **Frictionless Checkout (`GuestCheckoutScreen`):**
   - Full Name (اسم العميل أو الورشة)
   - Algerian Mobile Number (05, 06, or 07 with `PhoneValidator`)
   - Wilaya (58 Algerian Wilayas selector)
   - Commune & Detailed Delivery Address
   - Optional Customer Notes
6. **Order Confirmation (`OrderConfirmationScreen`):**
   - Unique Order Reference (e.g. `KGP-20261101-A1B2`)
   - Secure Tracking Token
   - Order breakdown
7. **Live Tracking (`OrderTrackingScreen`):**
   - Track order status (`PENDING`, `CONFIRMED`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`)
   - Access history of orders placed from the current device

---

## 3. Directory & File Structure

```text
mobile/
├── pubspec.yaml                       # Dependencies: provider, http, shared_preferences, intl, uuid
├── lib/
│   ├── main.dart                      # App entrypoint, MultiProvider setup, Arabic RTL localization
│   ├── core/
│   │   ├── constants/
│   │   │   └── app_constants.dart     # API URLs, Algerian wilayas list, storage keys
│   │   ├── theme/
│   │   │   └── app_theme.dart         # Dark brand theme, color palette, typography
│   │   └── utils/
│   │       ├── currency_formatter.dart # Algerian Dinar formatting (e.g. "8 500,00 د.ج")
│   │       └── phone_validator.dart   # Algerian mobile validation & normalization
│   ├── models/
│   │   ├── category.dart              # Spare-part category model
│   │   ├── product.dart               # Product catalog model
│   │   ├── cart_item.dart             # Cart line item model
│   │   └── guest_order.dart           # GuestOrderRequest & GuestOrderResponse models
│   ├── services/
│   │   ├── api_service.dart           # HTTP client, uniform envelope parser, guest checkout
│   │   └── cart_storage_service.dart  # Local SharedPreferences cart & order history
│   ├── providers/
│   │   ├── cart_provider.dart         # Persistent cart state management
│   │   ├── catalog_provider.dart      # Catalog products, categories, search state
│   │   └── order_provider.dart        # Order submission and status tracking
│   ├── screens/
│   │   ├── catalog_screen.dart        # Main browsing grid, search, category chips, cart badge
│   │   ├── product_detail_screen.dart # Detailed part info, quantity stepper, add-to-cart
│   │   ├── cart_screen.dart           # Cart review, quantity updates, total banner
│   │   ├── guest_checkout_screen.dart # Frictionless guest checkout form
│   │   ├── order_confirmation_screen.dart # Order reference, tracking token, summary
│   │   └── order_tracking_screen.dart # Live order tracking & local order history
│   └── widgets/
│       ├── product_card.dart          # Catalog product card with stock badges
│       ├── category_chips.dart        # Dynamic category filter chips
│       ├── cart_item_tile.dart        # Stepper row in cart screen
│       ├── empty_view.dart            # Empty state illustration widget
│       ├── error_view.dart            # Network/server error retry widget
│       └── loading_view.dart          # Emerald loading spinner
└── test/
    ├── cart_provider_test.dart        # Unit tests for cart additions, bounds, and totals
    ├── phone_validator_test.dart      # Unit tests for Algerian mobile format validation
    └── guest_order_model_test.dart    # Serialization and envelope parsing tests
```

---

## 4. Running the Application

### Prerequisites
- Flutter SDK (>= 3.0.0)
- Android Studio or VS Code with Flutter extension
- Android Emulator or physical device

### Configuration
By default, the application connects to the local backend:
- **Android Emulator:** `http://10.0.2.2:8000/api/v1`
- **Physical Device (LAN):** Pass your local machine's IP address:
  ```bash
  flutter run --dart-define=API_URL=http://192.168.1.100:8000/api/v1
  ```

### Running Tests
```bash
flutter test
```

### Building Android APK (Production & Testing)

1. **Build Debug APK (For quick testing on physical Android devices):**
   ```bash
   flutter build apk --debug --dart-define=API_URL=http://<YOUR_LAN_IP>:8000/api/v1
   ```
   The APK will be located at: `build/app/outputs/flutter-apk/app-debug.apk`

2. **Build Release APK (Production-ready):**
   ```bash
   flutter build apk --release --dart-define=API_URL=https://api.kgplist.dz/api/v1
   ```
   The APK will be located at: `build/app/outputs/flutter-apk/app-release.apk`

3. **Install directly onto connected Android device via USB:**
   ```bash
   adb install -r build/app/outputs/flutter-apk/app-release.apk
   ```

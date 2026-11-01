# KGP LIST — Data Model & Database Architecture

## 1. Overview

KGP LIST uses **PostgreSQL 16** managed through **SQLAlchemy 2.0** ORM and **Alembic** migrations. The schema is normalized, strictly typed, and enforced with table-level check constraints.

---

## 2. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    ADMIN_USER {
        bigint id PK
        string email UK
        string hashed_password
        string full_name
        string role
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CATEGORY {
        bigint id PK
        string name UK
        integer display_order
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    PRODUCT {
        bigint id PK
        string sku UK
        string name
        bigint category_id FK
        numeric selling_price
        integer available_quantity
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CUSTOMER {
        bigint id PK
        string full_name
        string phone_number UK
        string business_name
        string wilaya
        text address
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    ORDER {
        bigint id PK
        string order_reference UK
        bigint customer_id FK
        string status
        numeric total_amount
        text customer_notes
        timestamp created_at
        timestamp updated_at
    }

    ORDER_ITEM {
        bigint id PK
        bigint order_id FK
        bigint product_id FK
        string product_name
        string product_sku
        numeric unit_price
        integer quantity
        numeric total_price
        timestamp created_at
    }

    DEVICE_NOTIFICATION_TOKEN {
        bigint id PK
        string token UK
        string platform
        bigint customer_id FK
        bigint admin_user_id FK
        boolean is_active
        timestamp last_used_at
        timestamp created_at
    }

    AUDIT_LOG {
        bigint id PK
        string actor_type
        string actor_id
        string action
        string entity_type
        string entity_id
        json details
        string ip_address
        timestamp created_at
    }

    IDEMPOTENCY_KEY {
        bigint id PK
        string key UK
        string request_hash
        integer response_code
        text response_body
        timestamp created_at
        timestamp expires_at
    }

    CATEGORY ||--o{ PRODUCT : "classifies"
    CUSTOMER ||--o{ ORDER : "places"
    ORDER ||--|{ ORDER_ITEM : "contains"
    PRODUCT ||--o{ ORDER_ITEM : "referenced_by"
    CUSTOMER ||--o{ DEVICE_NOTIFICATION_TOKEN : "owns"
    ADMIN_USER ||--o{ DEVICE_NOTIFICATION_TOKEN : "owns"
```

---

## 3. Core Entities Detail

### 3.1. `products`
- **Purpose:** Spare-parts catalog items (Screens, Batteries, Flex cables, Charging boards, etc.).
- **Currency:** Algerian Dinars (DZD). Stored as `Numeric(12, 2)` to eliminate floating-point arithmetic rounding errors.
- **Constraints:**
  - `ck_products_selling_price_positive`: `selling_price >= 0`
  - `ck_products_quantity_positive`: `available_quantity IS NULL OR available_quantity >= 0`
- **Foreign Keys:** `category_id -> categories.id` with `ondelete="RESTRICT"` to prevent deleting categories with active products.

### 3.2. `orders` & `order_items` (Historical Snapshotting)
- **Immutable Historical Line Items:**
  When a customer places an order, the `order_items` record captures:
  - `product_name`
  - `product_sku`
  - `unit_price`
  - `quantity`
  - `total_price`
  
  **Why?** If an administrator renames a product from *"Samsung A51 Screen"* to *"Samsung A51 Screen OEM Refurbished"* or increases its price from `14,500.00 DZD` to `16,000.00 DZD`, previously submitted customer orders must **never** change.

- **Deletions / Discontinuations:**
  - `product_id` in `order_items` is configured with `ondelete="SET NULL"`. If a product is retired or deleted, the historical invoice and line item records remain intact for accounting.
  - `order_id` uses `ondelete="CASCADE"`. If an order is purged, its line items are cleaned up.

### 3.3. `customers`
- **Purpose:** Store owners, repair technicians, and retail customers.
- **Validation:** Algerian phone numbers are validated to ensure standard format (`05`, `06`, `07`, or `+213` with 8 digits).

### 3.4. `device_notification_tokens`
- **Purpose:** Store Firebase Cloud Messaging (FCM) registration tokens for customer Android devices and admin web/mobile clients.
- **Foreign Keys:** Soft cascades on `customer_id` or `admin_user_id`.

### 3.5. `audit_logs`
- **Purpose:** Security and auditability.
- **Attributes:** Captures actor type (`ADMIN`, `CUSTOMER`, `SYSTEM`), actor ID, entity modified, action performed, payload details (JSON), and IP address.

### 3.6. `idempotency_keys`
- **Purpose:** Duplicate request suppression and safe response replay.
- **Attributes:**
  - `key`: Unique client-supplied idempotency token (UUID).
  - `request_hash`: SHA-256 hash of `path|customer_id|payload` used to detect payload tampering or key reuse.
  - `response_code`: Cached HTTP status code (e.g. 201).
  - `response_body`: Cached JSON response payload.
  - `expires_at`: Expiration timestamp (default 24-hour retention).
- **Indexes:** Indexed on `key` (unique), `request_hash`, and `expires_at`.

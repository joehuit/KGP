# KGP LIST — API Guide & Contract (Phase 2B)

## 1. API Architecture

All client interactions occur through HTTP REST endpoints versioned under `/api/v1` (with the exception of `/api/health`).

- **Base URL (Local):** `http://localhost:8000`
- **Interactive OpenAPI Documentation (Swagger UI):** `http://localhost:8000/api/docs`
- **ReDoc Documentation:** `http://localhost:8000/api/redoc`

---

## 2. Standard Response Envelope

Successful requests always return a consistent JSON envelope:

```json
{
  "success": true,
  "message": "Optional descriptive message",
  "data": { ... }
}
```

Paginated collections wrap results with metadata:

```json
{
  "success": true,
  "message": null,
  "data": {
    "items": [ ... ],
    "meta": {
      "page": 1,
      "page_size": 20,
      "total_items": 142,
      "total_pages": 8
    }
  }
}
```

---

## 3. Standard Error Envelope

Failed requests never expose raw Python exception traces or internal database paths. They strictly return:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The submitted request payload contains invalid fields.",
    "details": [
      {
        "field": "body -> selling_price",
        "message": "Decimal input should have no more than 2 decimal places",
        "type": "decimal_max_places"
      }
    ],
    "timestamp": "2026-11-01T10:15:30.123456Z"
  }
}
```

Standard Error Codes:
- `NOT_FOUND` (404)
- `CONFLICT` (409)
- `VALIDATION_ERROR` (422)
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `TOO_MANY_REQUESTS` (429) — Includes `Retry-After: <seconds>` response header
- `INTERNAL_SERVER_ERROR` (500)
- `DATABASE_UNAVAILABLE` (503)

---

## 4. Authentication & Authorization Foundation

### Administrative Authentication (JWT)
Admins authenticate via email and password to receive a signed JWT access token:
- `POST /api/v1/auth/login` (or `/api/v1/auth/admin/login`)
- Header for authenticated calls: `Authorization: Bearer <access_token>`
- Token lifespan: 12 hours (configurable via `ADMIN_TOKEN_EXPIRE_MINUTES`).
- Revocation: `POST /api/v1/auth/logout` immediately invalidates the token via the `jti` blacklist.

### Temporary ADMIN_API_KEY Migration
- In `development` and `testing`: `X-Admin-Key` is accepted as a transitional bridge with deprecation logging.
- In `staging` and `production`: `X-Admin-Key` is **strictly rejected** with `401 Unauthorized`. All administrative requests must use JWT Bearer tokens.

### Role-Based Access Control (RBAC) Matrix

| Endpoint | Superadmin | Admin | Operator | Customer | Public |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `POST /api/v1/auth/login` | Allowed | Allowed | Allowed | N/A | Allowed |
| `POST /api/v1/auth/logout` | Allowed | Allowed | Allowed | N/A | N/A |
| `GET /api/v1/auth/me` | Allowed | Allowed | Allowed | N/A | N/A |
| `GET /api/v1/admin/users` | **Allowed** | Forbidden | Forbidden | Forbidden | Forbidden |
| `POST /api/v1/admin/users` | **Allowed** | Forbidden | Forbidden | Forbidden | Forbidden |
| `GET /api/v1/categories` | Allowed | Allowed | Allowed | Allowed | Allowed |
| `POST /api/v1/categories` | **Allowed** | **Allowed** | Forbidden | Forbidden | Forbidden |
| `PATCH /api/v1/categories/{id}` | **Allowed** | **Allowed** | Forbidden | Forbidden | Forbidden |
| `GET /api/v1/products` | Allowed | Allowed | Allowed | Allowed | Allowed |
| `POST /api/v1/products` | **Allowed** | **Allowed** | Forbidden | Forbidden | Forbidden |
| `PATCH /api/v1/products/{id}` | **Allowed** | **Allowed** | Forbidden | Forbidden | Forbidden |
| `POST /api/v1/customers` | Allowed | Allowed | Allowed | Allowed | Allowed |
| `GET /api/v1/customers/me` | N/A | N/A | N/A | **Self Only** | Forbidden |
| `GET /api/v1/customers/{id}` | Allowed | Allowed | Forbidden | Forbidden | Forbidden |
| `GET /api/v1/customers/by-phone/{phone}` | Allowed | Allowed | Forbidden | Forbidden | Forbidden |
| `POST /api/v1/orders` | Allowed | Allowed | Allowed | **Self Identity** | Allowed |
| `GET /api/v1/orders` | **All Orders** | **All Orders** | **All Orders** | **Self Only** | Forbidden |
| `GET /api/v1/orders/{id}` | **Any Order** | **Any Order** | **Any Order** | **Self Only** | Forbidden |
| `PATCH /api/v1/orders/{id}/status` | **Allowed** | **Allowed** | **Allowed** | Forbidden | Forbidden |

---

## 5. Customer Authentication & OTP Flow

1. **Request OTP:**
   - `POST /api/v1/auth/customer/request-otp`
   - Body: `{"phone_number": "0550123456"}`
   - Normalizes standard Algerian formats (`+213`, `00213`, `05`, `06`, `07`).
   - Rate limited to 3 requests per 10 minutes per phone number.
   - Dispatches a 6-digit numeric OTP via the configured SMS gateway. Valid for 5 minutes.

2. **Verify OTP:**
   - `POST /api/v1/auth/customer/verify-otp`
   - Body: `{"phone_number": "0550123456", "code": "123456"}`
   - Constant-time verification against salted SHA-256 OTP hash.
   - Max 3 attempts before challenge invalidation.
   - Returns customer access token (30-day lifespan).

3. **Customer Profile:**
   - `GET /api/v1/customers/me`
   - Header: `Authorization: Bearer <customer_token>`
   - Returns verified customer identity.

---

## 6. Order Ownership & Idempotency

### Order Ownership (IDOR Defense)
- When placing orders (`POST /api/v1/orders`): If a customer JWT is present, the server **derives `customer_id` strictly from the token claims**. Any spoofed `customer_id` sent in the request body is ignored.
- When listing orders (`GET /api/v1/orders`): Authenticated customers are strictly restricted to their own orders.
- When inspecting an order (`GET /api/v1/orders/{id}`): If the order belongs to another customer, the server returns `404 Not Found` to prevent leaking order existence.

### Idempotency Protection
To protect against duplicate order creation caused by network disconnects or retries, clients can provide the `Idempotency-Key` header:
- Header: `Idempotency-Key: <unique-uuid-or-client-token>`
- **First request:** Executes order transaction, persists result in `idempotency_keys` table, returns `201 Created`.
- **Subsequent identical request:** Returns the cached response immediately with header `Idempotent-Replay: true`, without creating duplicate order records.
- **Conflicting request (same key, differing payload):** Returns `409 Conflict` ("Idempotency key conflict").

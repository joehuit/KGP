# KGP LIST — Administration Dashboard

## Overview

The **Admin Web Dashboard** is a responsive web application designed for KGP LIST store managers, inventory operators, and administrators in Algeria.

> **Status:** Planned for Phase 2+. Do not implement full UI in Phase 1 per architecture roadmap.

## Architectural Role

1. **Catalog Management:**
   - Create, update, categorize, and deactivate spare-parts products.
   - Real-time price updating in Algerian Dinars (DZD).
   - Bulk Excel/XLSX import and export (planned for Phase 3).
2. **Order Management:**
   - Real-time order monitoring across Algerian wilayas.
   - Order lifecycle state updates (`PENDING` -> `CONFIRMED` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` or `CANCELLED`).
   - Customer profile inspection and order history tracking.
3. **Role-Based Access Control (RBAC):**
   - `superadmin`: Full system control, admin user provisioning, audit log inspection.
   - `admin`: Catalog management, order processing, customer management.
   - `operator`: Order status updates and fulfillment viewing.
4. **Audit Log Inspection:**
   - Complete visibility into administrative actions (price alterations, status overrides).

## Communication Architecture

- The admin dashboard communicates exclusively with the backend via HTTPS REST API endpoints under `/api/v1`.
- **Clients NEVER connect directly to PostgreSQL.**
- Standard authentication will utilize HTTP-only secure cookies / JWT bearer tokens in Phase 2.

## Technology Roadmap

- **Framework:** React / Vite or Next.js (TypeScript).
- **Styling:** Tailwind CSS with responsive desktop and tablet support.
- **State Management:** TanStack Query (React Query) for server caching and optimistic updates.
- **Form Validation:** Zod with strict decimal validation matching backend Pydantic schemas.

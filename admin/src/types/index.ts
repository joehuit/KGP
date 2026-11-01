// Common API Response Envelope
export interface ResponseEnvelope<T> {
  success: boolean;
  message?: string;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}

// User & Auth
export type AdminRole = 'superadmin' | 'admin' | 'operator';

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: AdminRole;
  is_active: boolean;
  permissions?: string[];
  created_at?: string;
}

export interface LoginResponseData {
  access_token: string;
  token_type: string;
  expires_in: number;
  role: AdminRole;
  user_id: number;
  full_name: string;
  permissions: string[];
}

// Categories
export interface Category {
  id: number;
  name: string;
  display_order: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CategoryCreate {
  name: string;
  display_order?: number;
  is_active?: boolean;
}

export interface CategoryUpdate {
  name?: string;
  display_order?: number;
  is_active?: boolean;
}

// Products
export interface Product {
  id: number;
  sku: string;
  name: string;
  category_id: number;
  category_name?: string;
  selling_price: string | number;
  available_quantity: number | null;
  description?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProductCreate {
  sku: string;
  name: string;
  category_id: number;
  selling_price: number | string;
  available_quantity?: number | null;
  description?: string | null;
  is_active?: boolean;
}

export interface ProductUpdate {
  sku?: string;
  name?: string;
  category_id?: number;
  selling_price?: number | string;
  available_quantity?: number | null;
  description?: string | null;
  is_active?: boolean;
}

// Excel Import
export interface ProductImportRow {
  row_index: number;
  sku: string;
  name: string;
  category_name: string;
  selling_price: string | number;
  available_quantity?: number | null;
  description?: string | null;
  status: 'new' | 'update' | 'invalid';
  errors: string[];
}

export interface ExcelImportPreviewResponse {
  filename: string;
  detected_columns: string[];
  column_mapping: Record<string, string | null>;
  total_rows: number;
  valid_count: number;
  invalid_count: number;
  new_products_count: number;
  update_products_count: number;
  new_categories: string[];
  rows: ProductImportRow[];
}

export interface ExcelImportCommitSummary {
  total_processed: number;
  created: number;
  updated: number;
  skipped: number;
  failed: number;
  errors: string[];
}

// Orders
export type OrderStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'PROCESSING'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'CANCELLED';

export interface OrderItem {
  id: number;
  product_id?: number | null;
  product_sku: string;
  product_name: string;
  unit_price: string | number;
  quantity: number;
  total_price: string | number;
}

export interface Order {
  id: number;
  order_reference: string;
  customer_id: number;
  status: OrderStatus;
  total_amount: string | number;
  customer_notes?: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

// Customers
export interface Customer {
  id: number;
  full_name: string;
  phone_number: string;
  business_name?: string | null;
  wilaya?: string | null;
  address?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CustomerUpdate {
  full_name?: string;
  phone_number?: string;
  business_name?: string | null;
  wilaya?: string | null;
  address?: string | null;
  is_active?: boolean;
}

// Audit Logs
export interface AuditLog {
  id: number;
  actor_type: string;
  actor_id?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  details?: any;
  ip_address?: string | null;
  created_at: string;
}

// Dashboard Statistics
export interface DashboardStats {
  total_products: number;
  total_categories: number;
  total_customers: number;
  total_orders: number;
  pending_orders: number;
  confirmed_orders: number;
  processing_orders: number;
  shipped_orders: number;
  delivered_orders: number;
  cancelled_orders: number;
  total_revenue: string | number;
  low_stock_count: number;
  low_stock_products: Product[];
  recent_orders: Order[];
}

// System Settings
export interface SystemSettings {
  project_name: string;
  project_description: string;
  version: string;
  environment: string;
  currency: string;
  currency_symbol: string;
  currency_name_ar: string;
  currency_name_fr: string;
  low_stock_threshold: number;
  admin_token_expire_minutes: number;
  customer_token_expire_minutes: number;
  sms_gateway_provider: string;
  supported_wilayas: { code: string; name_ar: string; name_fr: string }[];
}

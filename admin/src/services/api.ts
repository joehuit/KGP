import {
  AdminUser,
  AuditLog,
  Category,
  CategoryCreate,
  CategoryUpdate,
  Customer,
  CustomerUpdate,
  DashboardStats,
  ExcelImportCommitSummary,
  ExcelImportPreviewResponse,
  LoginResponseData,
  Order,
  OrderStatus,
  PaginatedResponse,
  Product,
  ProductCreate,
  ProductImportRow,
  ProductUpdate,
  ResponseEnvelope,
  SystemSettings,
} from '../types';

const BASE_URL = '/api/v1';

class ApiClient {
  private getToken(): string | null {
    return localStorage.getItem('kgp_admin_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      localStorage.removeItem('kgp_admin_token');
      localStorage.removeItem('kgp_admin_profile');
      window.dispatchEvent(new Event('auth:unauthorized'));
    }

    let body: any;
    try {
      body = await res.json();
    } catch {
      body = null;
    }

    if (!res.ok) {
      const errorMsg =
        body?.error?.message ||
        body?.message ||
        body?.detail ||
        `HTTP Error ${res.status}`;
      const err = new Error(errorMsg);
      (err as any).status = res.status;
      (err as any).data = body;
      throw err;
    }

    return (body?.data !== undefined ? body.data : body) as T;
  }

  // --- Auth Endpoints ---
  async login(payload: { email: string; password: string }): Promise<LoginResponseData> {
    return this.request<LoginResponseData>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getProfile(): Promise<AdminUser> {
    return this.request<AdminUser>('/auth/me');
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      localStorage.removeItem('kgp_admin_token');
      localStorage.removeItem('kgp_admin_profile');
    }
  }

  // --- Dashboard Endpoints ---
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/dashboard/stats');
  }

  // --- Categories Endpoints ---
  async listCategories(activeOnly = false): Promise<Category[]> {
    return this.request<Category[]>(`/categories?active_only=${activeOnly}`);
  }

  async createCategory(data: CategoryCreate): Promise<Category> {
    return this.request<Category>('/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCategory(id: number, data: CategoryUpdate): Promise<Category> {
    return this.request<Category>(`/categories/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteCategory(id: number): Promise<{ deleted: boolean; category_id: number }> {
    return this.request<{ deleted: boolean; category_id: number }>(`/categories/${id}`, {
      method: 'DELETE',
    });
  }

  // --- Products Endpoints ---
  async listProducts(params: {
    page?: number;
    page_size?: number;
    category_id?: number;
    search?: string;
    active_only?: boolean;
  } = {}): Promise<PaginatedResponse<Product>> {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());
    if (params.category_id) q.append('category_id', params.category_id.toString());
    if (params.search) q.append('search', params.search);
    if (params.active_only !== undefined) q.append('active_only', params.active_only.toString());

    return this.request<PaginatedResponse<Product>>(`/products?${q.toString()}`);
  }

  async getProduct(id: number): Promise<Product> {
    return this.request<Product>(`/products/${id}`);
  }

  async createProduct(data: ProductCreate): Promise<Product> {
    return this.request<Product>('/products', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProduct(id: number, data: ProductUpdate): Promise<Product> {
    return this.request<Product>(`/products/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteProduct(id: number): Promise<{ deleted: boolean; deactivated: boolean; message: string }> {
    return this.request<{ deleted: boolean; deactivated: boolean; message: string }>(`/products/${id}`, {
      method: 'DELETE',
    });
  }

  // --- Excel Import Endpoints ---
  async previewExcelImport(file: File): Promise<ExcelImportPreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<ExcelImportPreviewResponse>('/products/import/preview', {
      method: 'POST',
      body: formData,
    });
  }

  async commitExcelImport(payload: {
    items: ProductImportRow[];
    create_missing_categories: boolean;
    update_existing_products: boolean;
  }): Promise<ExcelImportCommitSummary> {
    return this.request<ExcelImportCommitSummary>('/products/import/commit', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- Orders Endpoints ---
  async listOrders(params: {
    page?: number;
    page_size?: number;
    customer_id?: number;
    status?: OrderStatus;
  } = {}): Promise<PaginatedResponse<Order>> {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());
    if (params.customer_id) q.append('customer_id', params.customer_id.toString());
    if (params.status) q.append('status', params.status);

    return this.request<PaginatedResponse<Order>>(`/orders?${q.toString()}`);
  }

  async getOrder(id: number): Promise<Order> {
    return this.request<Order>(`/orders/${id}`);
  }

  async updateOrderStatus(id: number, status: OrderStatus): Promise<Order> {
    return this.request<Order>(`/orders/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  // --- Customers Endpoints ---
  async listCustomers(params: {
    page?: number;
    page_size?: number;
    search?: string;
    wilaya?: string;
    active_only?: boolean;
  } = {}): Promise<PaginatedResponse<Customer>> {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());
    if (params.search) q.append('search', params.search);
    if (params.wilaya) q.append('wilaya', params.wilaya);
    if (params.active_only !== undefined) q.append('active_only', params.active_only.toString());

    return this.request<PaginatedResponse<Customer>>(`/customers?${q.toString()}`);
  }

  async getCustomer(id: number): Promise<Customer> {
    return this.request<Customer>(`/customers/${id}`);
  }

  async getCustomerOrders(
    customerId: number,
    params: { page?: number; page_size?: number } = {}
  ): Promise<PaginatedResponse<Order>> {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());

    return this.request<PaginatedResponse<Order>>(`/customers/${customerId}/orders?${q.toString()}`);
  }

  async updateCustomer(id: number, data: CustomerUpdate): Promise<Customer> {
    return this.request<Customer>(`/customers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // --- Admin Users (Superadmin Only) ---
  async listAdminUsers(params: { page?: number; page_size?: number } = {}): Promise<PaginatedResponse<AdminUser>> {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());

    return this.request<PaginatedResponse<AdminUser>>(`/auth/admin/users?${q.toString()}`);
  }

  async createAdminUser(data: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    is_active?: boolean;
  }): Promise<AdminUser> {
    return this.request<AdminUser>('/auth/admin/users', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAdminUser(
    id: number,
    data: {
      email?: string;
      password?: string;
      full_name?: string;
      role?: string;
      is_active?: boolean;
    }
  ): Promise<AdminUser> {
    return this.request<AdminUser>(`/auth/admin/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // --- Audit Logs (Superadmin Only) ---
  async listAuditLogs(params: {
    page?: number;
    page_size?: number;
    entity_type?: string;
    action?: string;
    actor_type?: string;
  } = {}): Promise<PaginatedResponse<AuditLog>> {
    const q = new URLSearchParams();
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());
    if (params.entity_type) q.append('entity_type', params.entity_type);
    if (params.action) q.append('action', params.action);
    if (params.actor_type) q.append('actor_type', params.actor_type);

    return this.request<PaginatedResponse<AuditLog>>(`/audit-logs?${q.toString()}`);
  }

  // --- Settings ---
  async getSettings(): Promise<SystemSettings> {
    return this.request<SystemSettings>('/settings');
  }
}

export const api = new ApiClient();

import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Eye,
  MapPin,
  Phone,
  RefreshCw,
  Search,
  ShoppingCart,
  Store,
  User,
  Users,
  X,
} from 'lucide-react';
import { Customer, Order } from '../types';
import { api } from '../services/api';
import { OrderStatusBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Pagination } from '../components/common/Pagination';
import { useToast } from '../components/common/Toast';

export const CustomersView: React.FC = () => {
  const { showToast } = useToast();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Pagination & Search
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  // Customer Orders Drawer
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerOrders, setCustomerOrders] = useState<Order[]>([]);
  const [isLoadingOrders, setIsLoadingOrders] = useState(false);

  const fetchCustomers = async () => {
    setIsLoading(true);
    try {
      const res = await api.listCustomers({
        page,
        page_size: pageSize,
        search: searchTerm.trim() || undefined,
      });
      setCustomers(res.items);
      setTotalPages(res.meta.total_pages);
      setTotalItems(res.meta.total_items);
    } catch (err: any) {
      showToast('تعذر استرجاع قائمة الزبائن: ' + err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchCustomers();
  };

  const openCustomerOrders = async (cust: Customer) => {
    setSelectedCustomer(cust);
    setIsLoadingOrders(true);
    try {
      const res = await api.getCustomerOrders(cust.id);
      setCustomerOrders(res.items);
    } catch (err: any) {
      showToast('تعذر استرجاع طلبيات الزبون: ' + err.message, 'error');
    } finally {
      setIsLoadingOrders(false);
    }
  };

  const formatPrice = (val: string | number) => {
    const num = typeof val === 'number' ? val : parseFloat(val);
    return isNaN(num) ? '0.00' : num.toLocaleString('fr-DZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-brand-400" />
              <span>دليل الزبائن وورشات الصيانة (Clients & Ateliers)</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              إدارة حسابات التقنيين والورشات المسجلة عبر التطبيق، مع تتبع سجل المشتريات
            </p>
          </div>

          <button
            onClick={fetchCustomers}
            className="p-2.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="تحديث"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="ابحث بالاسم، رقم الهاتف (05/06/07)، اسم الورشة، أو الولاية..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-800/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500"
          />
          <button
            type="submit"
            className="absolute left-3 top-2.5 text-slate-400 hover:text-white"
          >
            <Search className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Customers Table */}
      {isLoading ? (
        <LoadingSpinner message="جاري استرجاع سجلات الزبائن..." />
      ) : customers.length === 0 ? (
        <EmptyState
          title="لم يتم العثور على زبائن"
          description="لا توجد حسابات زبائن مطابقة لعبارة البحث الحالية."
          icon={<Users className="w-10 h-10" />}
        />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead>
                <tr className="bg-slate-950/60 border-b border-slate-800 text-slate-400">
                  <th className="py-3.5 pr-5 font-bold">المعرف</th>
                  <th className="py-3.5 px-4 font-bold">اسم الزبون / التقني</th>
                  <th className="py-3.5 px-4 font-bold">رقم الهاتف</th>
                  <th className="py-3.5 px-4 font-bold">اسم الورشة / المحل</th>
                  <th className="py-3.5 px-4 font-bold">الولاية (Wilaya)</th>
                  <th className="py-3.5 px-4 font-bold">الحالة</th>
                  <th className="py-3.5 pl-5 font-bold text-left">سجل الطلبيات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {customers.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 pr-5 font-mono text-slate-400 font-bold">
                      #{c.id}
                    </td>
                    <td className="py-3.5 px-4 text-white font-bold text-sm">
                      {c.full_name}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-brand-300 dir-ltr text-right">
                      {c.phone_number}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {c.business_name || <span className="text-slate-500">غير محدد</span>}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {c.wilaya ? (
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-500" />
                          <span>{c.wilaya}</span>
                        </span>
                      ) : (
                        <span className="text-slate-500">غير محدد</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      {c.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          نشط (Actif)
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          معطل (Inactif)
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 pl-5 text-left">
                      <button
                        onClick={() => openCustomerOrders(c)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-300 text-xs font-semibold transition-colors"
                      >
                        <ShoppingCart className="w-3.5 h-3.5" />
                        <span>سجل المشتريات</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination
            page={page}
            totalPages={totalPages}
            totalItems={totalItems}
            pageSize={pageSize}
            onPageChange={(p) => setPage(p)}
          />
        </div>
      )}

      {/* Customer Orders History Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl relative my-8">
            <button
              onClick={() => setSelectedCustomer(null)}
              className="absolute left-6 top-6 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Customer Details Summary */}
            <div className="border-b border-slate-800 pb-5 mb-5">
              <h3 className="text-lg font-black text-white flex items-center gap-2 mb-1">
                <span>سجل طلبيات: {selectedCustomer.full_name}</span>
              </h3>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 font-mono mt-2">
                <span>الهاتف: {selectedCustomer.phone_number}</span>
                {selectedCustomer.business_name && (
                  <span>المحل: {selectedCustomer.business_name}</span>
                )}
                {selectedCustomer.wilaya && (
                  <span>الولاية: {selectedCustomer.wilaya}</span>
                )}
              </div>
            </div>

            {/* Orders list */}
            {isLoadingOrders ? (
              <LoadingSpinner message="جاري استرداد تاريخ الطلبيات..." />
            ) : customerOrders.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm bg-slate-950/60 rounded-2xl border border-dashed border-slate-800">
                لم يقم هذا الزبون بتقديم أي طلبية بعد.
              </div>
            ) : (
              <div className="bg-slate-950/80 rounded-2xl border border-slate-800 overflow-hidden max-h-96 overflow-y-auto">
                <table className="w-full text-right text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/60">
                      <th className="py-2.5 pr-4 font-bold">رقم الطلب</th>
                      <th className="py-2.5 px-3 font-bold">التاريخ</th>
                      <th className="py-2.5 px-3 font-bold">عدد البنود</th>
                      <th className="py-2.5 px-3 font-bold">المجموع الكلي</th>
                      <th className="py-2.5 pl-4 font-bold text-left">الحالة</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-medium">
                    {customerOrders.map((ord) => (
                      <tr key={ord.id}>
                        <td className="py-2.5 pr-4 font-mono text-white font-bold">
                          {ord.order_reference}
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 font-mono">
                          {new Date(ord.created_at).toLocaleDateString('fr-DZ')}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {ord.items?.length || 0} قطع
                        </td>
                        <td className="py-2.5 px-3 font-bold text-emerald-400 font-mono">
                          {formatPrice(ord.total_amount)} د.ج
                        </td>
                        <td className="py-2.5 pl-4 text-left">
                          <OrderStatusBadge status={ord.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

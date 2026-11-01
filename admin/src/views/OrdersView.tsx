import React, { useEffect, useState } from 'react';
import {
  Calendar,
  CheckCircle,
  Eye,
  Filter,
  Package,
  Phone,
  RefreshCw,
  Search,
  ShoppingCart,
  User,
  X,
} from 'lucide-react';
import { Order, OrderStatus } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { OrderStatusBadge } from '../components/common/Badge';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Pagination } from '../components/common/Pagination';
import { useToast } from '../components/common/Toast';

export const OrdersView: React.FC = () => {
  const { canUpdateOrders } = useAuth();
  const { showToast } = useToast();

  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters & Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [statusFilter, setStatusFilter] = useState<OrderStatus | undefined>(undefined);

  // Detail Modal
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);

  // Status Change Confirmation
  const [statusUpdateTarget, setStatusUpdateTarget] = useState<{
    orderId: number;
    newStatus: OrderStatus;
  } | null>(null);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  const fetchOrders = async () => {
    setIsLoading(true);
    try {
      const res = await api.listOrders({
        page,
        page_size: pageSize,
        status: statusFilter,
      });
      setOrders(res.items);
      setTotalPages(res.meta.total_pages);
      setTotalItems(res.meta.total_items);
    } catch (err: any) {
      showToast('تعذر استرداد قائمة الطلبات: ' + err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [page, statusFilter]);

  const handleConfirmStatusChange = async () => {
    if (!statusUpdateTarget) return;
    setIsUpdatingStatus(true);
    try {
      const updated = await api.updateOrderStatus(
        statusUpdateTarget.orderId,
        statusUpdateTarget.newStatus
      );
      showToast(`تم تحديث حالة الطلب إلى "${updated.status}" بنجاح.`, 'success');
      setStatusUpdateTarget(null);
      if (selectedOrder && selectedOrder.id === updated.id) {
        setSelectedOrder(updated);
      }
      fetchOrders();
    } catch (err: any) {
      showToast(err.message || 'فشل تحديث حالة الطلب.', 'error');
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const formatPrice = (val: string | number) => {
    const num = typeof val === 'number' ? val : parseFloat(val);
    return isNaN(num) ? '0.00' : num.toLocaleString('fr-DZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const getNextStatuses = (current: OrderStatus): OrderStatus[] => {
    switch (current) {
      case 'PENDING':
        return ['CONFIRMED', 'CANCELLED'];
      case 'CONFIRMED':
        return ['PROCESSING', 'CANCELLED'];
      case 'PROCESSING':
        return ['SHIPPED', 'CANCELLED'];
      case 'SHIPPED':
        return ['DELIVERED', 'CANCELLED'];
      case 'DELIVERED':
      case 'CANCELLED':
        return [];
      default:
        return [];
    }
  };

  const getStatusLabel = (s: OrderStatus): string => {
    switch (s) {
      case 'PENDING':
        return 'قيد الانتظار (En attente)';
      case 'CONFIRMED':
        return 'مؤكد (Confirmé)';
      case 'PROCESSING':
        return 'قيد التحضير (En préparation)';
      case 'SHIPPED':
        return 'تم الشحن (Expédié)';
      case 'DELIVERED':
        return 'تم التسليم (Livré)';
      case 'CANCELLED':
        return 'ملغى (Annulé)';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 transition-colors">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-brand-600 dark:text-brand-400" />
              <span>إدارة وتتبع طلبيات الزبائن (Commandes)</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              متابعة مراحل تأكيد الطلبات، تحضير قطع الغيار، والشحن للورشات عبر الولايات
            </p>
          </div>

          <button
            onClick={fetchOrders}
            className="p-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
            title="تحديث"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Status Filters Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-200 dark:border-slate-800/80">
          <button
            onClick={() => {
              setStatusFilter(undefined);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              statusFilter === undefined
                ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/30'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 dark:border-transparent dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
            }`}
          >
            الكل (Toutes)
          </button>
          {(
            [
              'PENDING',
              'CONFIRMED',
              'PROCESSING',
              'SHIPPED',
              'DELIVERED',
              'CANCELLED',
            ] as OrderStatus[]
          ).map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                statusFilter === st
                  ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/30'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 dark:border-transparent dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
              }`}
            >
              {getStatusLabel(st)}
            </button>
          ))}
        </div>
      </div>

      {/* Orders Table */}
      {isLoading ? (
        <LoadingSpinner message="جاري استرجاع قائمة الطلبات..." />
      ) : orders.length === 0 ? (
        <EmptyState
          title="لا توجد طلبات تطابق هذا التصنيف"
          description="لم يتم العثور على أي طلبيات بالحالة المختارة حالياً."
          icon={<ShoppingCart className="w-10 h-10" />}
        />
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm transition-colors">
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                  <th className="py-3.5 pr-5 font-bold">المرجع (Référence)</th>
                  <th className="py-3.5 px-4 font-bold">التاريخ والتوقيت</th>
                  <th className="py-3.5 px-4 font-bold">معرف الزبون</th>
                  <th className="py-3.5 px-4 font-bold">عدد البنود</th>
                  <th className="py-3.5 px-4 font-bold">المجموع (DZD)</th>
                  <th className="py-3.5 px-4 font-bold">الحالة</th>
                  <th className="py-3.5 pl-5 font-bold text-left">التفاصيل</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/60 font-medium">
                {orders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 pr-5 font-mono text-slate-900 dark:text-white font-bold">
                      {ord.order_reference}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 dark:text-slate-400 font-mono">
                      {new Date(ord.created_at).toLocaleDateString('fr-DZ', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3.5 px-4 text-slate-700 dark:text-slate-300 font-mono">
                      #{ord.customer_id}
                    </td>
                    <td className="py-3.5 px-4 text-slate-700 dark:text-slate-300">
                      {ord.items?.length || 0} قطع
                    </td>
                    <td className="py-3.5 px-4 font-bold text-emerald-600 dark:text-emerald-400 text-sm">
                      {formatPrice(ord.total_amount)} د.ج
                    </td>
                    <td className="py-3.5 px-4">
                      <OrderStatusBadge status={ord.status} />
                    </td>
                    <td className="py-3.5 pl-5 text-left">
                      <button
                        onClick={() => setSelectedOrder(ord)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-brand-700 dark:text-brand-300 border border-slate-200 dark:border-transparent text-xs font-semibold transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>معاينة الفاتورة</span>
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

      {/* Order Details Drawer / Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/75 backdrop-blur-sm animate-fade-in overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl relative my-8 transition-colors">
            <button
              onClick={() => setSelectedOrder(null)}
              className="absolute left-6 top-6 text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800 p-1 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Header info */}
            <div className="border-b border-slate-200 dark:border-slate-800 pb-5 mb-5">
              <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-xl font-black text-slate-900 dark:text-white">
                  {selectedOrder.order_reference}
                </span>
                <OrderStatusBadge status={selectedOrder.status} />
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                تم تقديم الطلب بتاريخ:{' '}
                {new Date(selectedOrder.created_at).toLocaleString('fr-DZ')}
              </p>
            </div>

            {/* Customer & Notes */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 block mb-1">
                  معلومات الزبون (Client)
                </span>
                <div className="text-sm font-bold text-slate-900 dark:text-white">
                  معرف الزبون: #{selectedOrder.customer_id}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 block mb-1">
                  ملاحظات الزبون (Notes)
                </span>
                <div className="text-xs text-slate-700 dark:text-slate-300">
                  {selectedOrder.customer_notes || 'لا توجد ملاحظات إضافية'}
                </div>
              </div>
            </div>

            {/* Line Items Table with Historical Snapshots */}
            <div className="mb-6">
              <h5 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-3">
                تفاصيل البنود والأسعار المسجلة تاريخياً (Lignes de commande)
              </h5>
              <div className="bg-slate-50 dark:bg-slate-950/80 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                <table className="w-full text-right text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-900/60">
                      <th className="py-2.5 pr-4 font-bold">كود القطعة</th>
                      <th className="py-2.5 px-3 font-bold">اسم القطعة والموديل</th>
                      <th className="py-2.5 px-3 font-bold">سعر الوحدة</th>
                      <th className="py-2.5 px-3 font-bold">الكمية</th>
                      <th className="py-2.5 pl-4 font-bold text-left">المجموع</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-medium">
                    {selectedOrder.items?.map((it) => (
                      <tr key={it.id}>
                        <td className="py-2.5 pr-4 font-mono text-brand-600 dark:text-brand-300 font-bold">
                          {it.product_sku}
                        </td>
                        <td className="py-2.5 px-3 text-slate-900 dark:text-white">{it.product_name}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-700 dark:text-slate-300">
                          {formatPrice(it.unit_price)} د.ج
                        </td>
                        <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-white">
                          &times; {it.quantity}
                        </td>
                        <td className="py-2.5 pl-4 text-left font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                          {formatPrice(it.total_price)} د.ج
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-slate-100 dark:bg-slate-900/80 border-t border-slate-200 dark:border-slate-800 font-bold text-sm">
                      <td colSpan={4} className="py-3 pr-4 text-slate-900 dark:text-white">
                        المجموع الإجمالي للطلب (Total TTC):
                      </td>
                      <td className="py-3 pl-4 text-left text-emerald-600 dark:text-emerald-400 font-mono text-base font-black">
                        {formatPrice(selectedOrder.total_amount)} د.ج
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* State Machine Action Controls */}
            {canUpdateOrders && (
              <div className="border-t border-slate-200 dark:border-slate-800 pt-5">
                <span className="text-xs font-bold text-slate-600 dark:text-slate-400 block mb-2">
                  تحديث حالة الطلب (Changer le statut):
                </span>
                <div className="flex flex-wrap gap-2">
                  {getNextStatuses(selectedOrder.status).map((nxt) => (
                    <button
                      key={nxt}
                      onClick={() =>
                        setStatusUpdateTarget({
                          orderId: selectedOrder.id,
                          newStatus: nxt,
                        })
                      }
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-md ${
                        nxt === 'CANCELLED'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-600 hover:text-white dark:bg-rose-600/20 dark:text-rose-300 dark:border-rose-500/30 dark:hover:bg-rose-600 dark:hover:text-white'
                          : 'bg-brand-600 hover:bg-brand-500 text-white shadow-brand-900/30'
                      }`}
                    >
                      تحويل إلى: {getStatusLabel(nxt)}
                    </button>
                  ))}
                  {getNextStatuses(selectedOrder.status).length === 0 && (
                    <span className="text-xs text-slate-500">
                      وصل الطلب إلى حالته النهائية (لا توجد انتقالات إضافية).
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Status Update Confirmation Modal */}
      <ConfirmModal
        isOpen={!!statusUpdateTarget}
        title="تأكيد تحديث حالة الطلب"
        message={`هل أنت متأكد من تغيير حالة الطلب إلى "${
          statusUpdateTarget ? getStatusLabel(statusUpdateTarget.newStatus) : ''
        }"؟`}
        confirmLabel="تأكيد التغيير"
        cancelLabel="إلغاء"
        isDestructive={statusUpdateTarget?.newStatus === 'CANCELLED'}
        isLoading={isUpdatingStatus}
        onConfirm={handleConfirmStatusChange}
        onCancel={() => setStatusUpdateTarget(null)}
      />
    </div>
  );
};

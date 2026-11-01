import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  CheckCircle2,
  Clock,
  Coins,
  FolderTree,
  Package,
  RefreshCw,
  ShoppingCart,
  TrendingUp,
  Truck,
  Users,
} from 'lucide-react';
import { DashboardStats } from '../types';
import { api } from '../services/api';
import { OrderStatusBadge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useToast } from '../components/common/Toast';
import { NavTab } from '../components/layout/Sidebar';

interface DashboardViewProps {
  onNavigate: (tab: NavTab) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const { showToast } = useToast();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err: any) {
      showToast('تعذر تحميل إحصائيات لوحة القيادة: ' + err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (isLoading || !stats) {
    return <LoadingSpinner message="جاري استرداد مؤشرات الأعمال..." />;
  }

  const formatPrice = (val: string | number) => {
    const num = typeof val === 'number' ? val : parseFloat(val);
    return isNaN(num) ? '0.00' : num.toLocaleString('fr-DZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Refresh */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>مرحباً بك في لوحة تحكم KGP BELFORT</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            جميع المؤشرات والأرقام المعروضة مستخرجة مباشرة من قاعدة بيانات PostgreSQL
          </p>
        </div>
        <button
          onClick={fetchStats}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-bold border border-slate-700 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>تحديث الإحصائيات (Actualiser)</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Products */}
        <div
          onClick={() => onNavigate('products')}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-brand-500/50 transition-all cursor-pointer group shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400">إجمالي قطع الغيار</span>
            <div className="p-2.5 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 group-hover:scale-110 transition-transform">
              <Boxes className="w-5 h-5" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">{stats.total_products}</div>
          <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
            <span>{stats.total_categories} فئات مصنفة</span>
            <ArrowRight className="w-4 h-4 text-brand-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Total Orders */}
        <div
          onClick={() => onNavigate('orders')}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-amber-500/50 transition-all cursor-pointer group shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400">إجمالي الطلبات</span>
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 group-hover:scale-110 transition-transform">
              <ShoppingCart className="w-5 h-5" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">{stats.total_orders}</div>
          <div className="flex items-center justify-between text-xs text-amber-400 font-medium mt-2">
            <span>{stats.pending_orders} طلب قيد الانتظار</span>
            <ArrowRight className="w-4 h-4 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Total Revenue */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400">حجم المبيعات المحققة</span>
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Coins className="w-5 h-5" />
            </div>
          </div>
          <div className="text-2xl font-black text-emerald-400">
            {formatPrice(stats.total_revenue)}{' '}
            <span className="text-xs font-bold text-slate-400">د.ج</span>
          </div>
          <div className="text-xs text-slate-400 mt-2">
            من الطلبات المؤكدة والمسلّمة
          </div>
        </div>

        {/* Registered Customers */}
        <div
          onClick={() => onNavigate('customers')}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-cyan-500/50 transition-all cursor-pointer group shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400">الزبائن والورشات</span>
            <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 group-hover:scale-110 transition-transform">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">{stats.total_customers}</div>
          <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
            <span>ورشات صيانة وتقنيين</span>
            <ArrowRight className="w-4 h-4 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </div>

      {/* Two Column Layout: Orders Distribution & Low Stock Alert */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Order Status Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-400" />
              <span>توزيع حالات الطلبات (État des commandes)</span>
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-800">
                <span className="text-xs text-amber-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  <span>قيد الانتظار (En attente)</span>
                </span>
                <span className="font-bold text-white text-sm">{stats.pending_orders}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-800">
                <span className="text-xs text-brand-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-brand-400" />
                  <span>مؤكد (Confirmé)</span>
                </span>
                <span className="font-bold text-white text-sm">{stats.confirmed_orders}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-800">
                <span className="text-xs text-cyan-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" />
                  <span>قيد التحضير / الشحن (En cours / Expédié)</span>
                </span>
                <span className="font-bold text-white text-sm">
                  {stats.processing_orders + stats.shipped_orders}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-800">
                <span className="text-xs text-emerald-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span>تم التسليم (Livré)</span>
                </span>
                <span className="font-bold text-white text-sm">{stats.delivered_orders}</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onNavigate('orders')}
            className="w-full mt-4 py-2.5 px-4 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-bold transition-colors"
          >
            عرض كافة الطلبات
          </button>
        </div>

        {/* Low Stock Alerts */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>تنبيهات انخفاض المخزون (Stock critique &le; 5)</span>
            </h4>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold">
              {stats.low_stock_count} قطع تحتاج تزويد
            </span>
          </div>

          {stats.low_stock_products.length === 0 ? (
            <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-white">المخزون متوازن</p>
              <p className="text-xs text-slate-400">لا توجد قطع غيار تحت العتبة الحرجة حالياً.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-right text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-3 pr-2 font-bold">رمز القطعة (SKU)</th>
                    <th className="pb-3 font-bold">اسم القطعة والموديل</th>
                    <th className="pb-3 font-bold">سعر البيع</th>
                    <th className="pb-3 pl-2 font-bold text-left">الكمية المتبقية</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {stats.low_stock_products.map((prod) => (
                    <tr key={prod.id} className="hover:bg-slate-800/40">
                      <td className="py-2.5 pr-2 font-mono text-brand-300 font-bold">
                        {prod.sku}
                      </td>
                      <td className="py-2.5 text-white">{prod.name}</td>
                      <td className="py-2.5 text-slate-300">{formatPrice(prod.selling_price)} د.ج</td>
                      <td className="py-2.5 pl-2 text-left">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                          {prod.available_quantity ?? 0} قطع
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Recent Orders Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-bold text-white flex items-center gap-2">
            <ShoppingCart className="w-4 h-4 text-brand-400" />
            <span>آخر الطلبات المسجلة (Dernières commandes)</span>
          </h4>
          <button
            onClick={() => onNavigate('orders')}
            className="text-xs font-bold text-brand-400 hover:text-brand-300 flex items-center gap-1"
          >
            <span>عرض الكل</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {stats.recent_orders.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            لا توجد طلبات مسجلة بعد في النظام.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="pb-3 pr-2 font-bold">رقم الطلب (Référence)</th>
                  <th className="pb-3 font-bold">التاريخ</th>
                  <th className="pb-3 font-bold">عدد البنود</th>
                  <th className="pb-3 font-bold">المجموع الكلي</th>
                  <th className="pb-3 pl-2 font-bold text-left">الحالة</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {stats.recent_orders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-slate-800/40">
                    <td className="py-3 pr-2 font-mono text-white font-bold">
                      {ord.order_reference}
                    </td>
                    <td className="py-3 text-slate-400 font-mono">
                      {new Date(ord.created_at).toLocaleDateString('fr-DZ', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3 text-slate-300">
                      {ord.items?.length || 0} قطعة
                    </td>
                    <td className="py-3 font-bold text-emerald-400">
                      {formatPrice(ord.total_amount)} د.ج
                    </td>
                    <td className="py-3 pl-2 text-left">
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
  );
};

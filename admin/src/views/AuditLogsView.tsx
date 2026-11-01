import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Eye,
  FileText,
  Filter,
  History,
  RefreshCw,
  Shield,
  ShieldAlert,
  User,
} from 'lucide-react';
import { AuditLog } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Pagination } from '../components/common/Pagination';
import { useToast } from '../components/common/Toast';

export const AuditLogsView: React.FC = () => {
  const { isSuperAdmin } = useAuth();
  const { showToast } = useToast();

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Pagination & Filters
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [entityFilter, setEntityFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const res = await api.listAuditLogs({
        page,
        page_size: pageSize,
        entity_type: entityFilter.trim() || undefined,
        action: actionFilter.trim() || undefined,
      });
      setLogs(res.items);
      setTotalPages(res.meta.total_pages);
      setTotalItems(res.meta.total_items);
    } catch (err: any) {
      showToast('تعذر استرجاع سجلات التدقيق: ' + err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isSuperAdmin) {
      fetchLogs();
    }
  }, [page, entityFilter, actionFilter, isSuperAdmin]);

  if (!isSuperAdmin) {
    return (
      <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-2xl">
        <ShieldAlert className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white mb-1">صلاحية غير كافية</h3>
        <p className="text-xs text-slate-400">
          سجلات التدقيق الأمني ومراقبة العمليات مخصصة فقط للمدير العام (Superadmin).
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <History className="w-5 h-5 text-brand-400" />
              <span>سجلات التدقيق الأمني والرقابة الإدارية (Audit Logs)</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              سجل غير قابل للتعديل يوثق جميع العمليات الحساسة (استيراد Excel، حذف المنتجات، التعديلات)
            </p>
          </div>

          <button
            onClick={fetchLogs}
            className="p-2.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="تحديث"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80">
          <div>
            <select
              value={entityFilter}
              onChange={(e) => {
                setEntityFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-brand-500"
            >
              <option value="">كافة الكيانات (PRODUCT, CATEGORY, ORDER...)</option>
              <option value="PRODUCT">المنتجات (PRODUCT)</option>
              <option value="CATEGORY">التصنيفات (CATEGORY)</option>
              <option value="ORDER">الطلبات (ORDER)</option>
              <option value="ADMIN_USER">المشرفين (ADMIN_USER)</option>
            </select>
          </div>

          <div>
            <input
              type="text"
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(1);
              }}
              placeholder="تصفية حسب نوع الإجراء (EXCEL_IMPORT, DELETE, STATUS_UPDATE)..."
              className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>
        </div>
      </div>

      {/* Logs Table */}
      {isLoading ? (
        <LoadingSpinner message="جاري استرجاع سجلات التدقيق..." />
      ) : logs.length === 0 ? (
        <EmptyState
          title="لا توجد سجلات تدقيق حالياً"
          description="لم تسجل أي عمليات مطابقة للمرشحات المحددة."
          icon={<History className="w-10 h-10" />}
        />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead>
                <tr className="bg-slate-950/60 border-b border-slate-800 text-slate-400">
                  <th className="py-3.5 pr-5 font-bold">التاريخ والتوقيت</th>
                  <th className="py-3.5 px-4 font-bold">الفاعل (Actor)</th>
                  <th className="py-3.5 px-4 font-bold">العملية (Action)</th>
                  <th className="py-3.5 px-4 font-bold">الكيان المستهدف</th>
                  <th className="py-3.5 px-4 font-bold">عنوان IP</th>
                  <th className="py-3.5 pl-5 font-bold text-left">التفاصيل الفنية</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 pr-5 font-mono text-slate-400">
                      {new Date(log.created_at).toLocaleString('fr-DZ')}
                    </td>
                    <td className="py-3.5 px-4 font-bold text-brand-300">
                      {log.actor_type}:{log.actor_id || 'System'}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-mono px-2 py-0.5 rounded bg-slate-800 text-white font-bold border border-slate-700 text-[11px]">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {log.entity_type} {log.entity_id ? `(#${log.entity_id})` : ''}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-500">
                      {log.ip_address || 'local'}
                    </td>
                    <td className="py-3.5 pl-5 text-left font-mono text-[10px] text-slate-400 max-w-xs truncate">
                      {log.details ? JSON.stringify(log.details) : '—'}
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
    </div>
  );
};

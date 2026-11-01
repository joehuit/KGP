import React, { useEffect, useState } from 'react';
import {
  CheckCircle,
  Edit2,
  Lock,
  Mail,
  Plus,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  User,
  UserCheck,
  UserPlus,
  UserX,
} from 'lucide-react';
import { AdminRole, AdminUser } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Pagination } from '../components/common/Pagination';
import { useToast } from '../components/common/Toast';

export const AdminUsersView: React.FC = () => {
  const { isSuperAdmin, user: currentUser } = useAuth();
  const { showToast } = useToast();

  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState<AdminUser | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<AdminRole>('admin');
  const [isActive, setIsActive] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchAdmins = async () => {
    setIsLoading(true);
    try {
      const res = await api.listAdminUsers({ page, page_size: pageSize });
      setAdmins(res.items);
      setTotalPages(res.meta.total_pages);
      setTotalItems(res.meta.total_items);
    } catch (err: any) {
      showToast('تعذر استرجاع حسابات المشرفين: ' + err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isSuperAdmin) {
      fetchAdmins();
    }
  }, [page, isSuperAdmin]);

  if (!isSuperAdmin) {
    return (
      <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-2xl">
        <ShieldAlert className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white mb-1">صلاحية غير كافية</h3>
        <p className="text-xs text-slate-400">
          إدارة المشرفين وصلاحيات النظام مخصصة حصرياً للمدير العام (Superadmin).
        </p>
      </div>
    );
  }

  const openCreateModal = () => {
    setEditingAdmin(null);
    setEmail('');
    setPassword('');
    setFullName('');
    setRole('admin');
    setIsActive(true);
    setIsModalOpen(true);
  };

  const openEditModal = (adm: AdminUser) => {
    setEditingAdmin(adm);
    setEmail(adm.email);
    setPassword(''); // leave blank if unchanged
    setFullName(adm.full_name);
    setRole(adm.role);
    setIsActive(adm.is_active);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !fullName.trim()) {
      showToast('البريد والاسم مطلوبان.', 'error');
      return;
    }

    if (!editingAdmin && (!password || password.length < 8)) {
      showToast('كلمة المرور مطلوبة وتتطلب 8 أحرف على الأقل.', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      if (editingAdmin) {
        await api.updateAdminUser(editingAdmin.id, {
          email: email.trim(),
          full_name: fullName.trim(),
          role,
          is_active: isActive,
          password: password ? password : undefined,
        });
        showToast('تم تحديث بيانات المشرف بنجاح.', 'success');
      } else {
        await api.createAdminUser({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
          role,
          is_active: isActive,
        });
        showToast('تم إنشاء حساب المشرف بنجاح.', 'success');
      }
      setIsModalOpen(false);
      fetchAdmins();
    } catch (err: any) {
      showToast(err.message || 'فشلت عملية حفظ المشرف.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleAdminStatus = async (adm: AdminUser) => {
    if (adm.id === currentUser?.id) {
      showToast('لا يمكنك تعطيل حسابك الخاص كمدير عام.', 'error');
      return;
    }
    try {
      await api.updateAdminUser(adm.id, { is_active: !adm.is_active });
      showToast(
        `تم ${!adm.is_active ? 'تفعيل' : 'تعطيل'} حساب "${adm.full_name}" بنجاح.`,
        'success'
      );
      fetchAdmins();
    } catch (err: any) {
      showToast(err.message || 'فشل تغيير حالة المشرف.', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm transition-colors">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-brand-600 dark:text-brand-400" />
            <span>إدارة حسابات المشرفين وصلاحيات RBAC</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            صلاحية حصرية للمدير العام (Superadmin) لتعيين المشرفين (Admin) ومشغلي الطلبيات (Operator)
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            onClick={fetchAdmins}
            className="p-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
            title="تحديث"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={openCreateModal}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-lg shadow-brand-900/30 transition-all flex-1 sm:flex-none"
          >
            <UserPlus className="w-4 h-4" />
            <span>إنشاء مشرف جديد (Nouvel admin)</span>
          </button>
        </div>
      </div>

      {/* Admins Table */}
      {isLoading ? (
        <LoadingSpinner message="جاري استرجاع حسابات المشرفين..." />
      ) : admins.length === 0 ? (
        <EmptyState
          title="لا يوجد مشرفين إضافيين"
          description="يمكنك إنشاء حسابات جديدة لمديري المبيعات ومشغلي المستودع."
          action={{ label: 'إنشاء أول حساب', onClick: openCreateModal }}
          icon={<ShieldCheck className="w-10 h-10" />}
        />
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm transition-colors">
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                  <th className="py-3.5 pr-5 font-bold">المعرف</th>
                  <th className="py-3.5 px-4 font-bold">الاسم الكامل</th>
                  <th className="py-3.5 px-4 font-bold">البريد الإلكتروني</th>
                  <th className="py-3.5 px-4 font-bold">الدور (Rôle)</th>
                  <th className="py-3.5 px-4 font-bold">الحالة</th>
                  <th className="py-3.5 pl-5 font-bold text-left">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/60 font-medium">
                {admins.map((adm) => (
                  <tr key={adm.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 pr-5 font-mono text-slate-500 dark:text-slate-400 font-bold">
                      #{adm.id}
                    </td>
                    <td className="py-3.5 px-4 text-slate-900 dark:text-white font-bold text-sm">
                      {adm.full_name}
                      {adm.id === currentUser?.id && (
                        <span className="mr-2 text-[10px] text-brand-600 dark:text-brand-400 font-normal">
                          (حسابك الحالي)
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-700 dark:text-slate-300 dir-ltr text-right">
                      {adm.email}
                    </td>
                    <td className="py-3.5 px-4">
                      {adm.role === 'superadmin' ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-500/15 dark:text-purple-300 dark:border-purple-500/30">
                          مدير عام (Superadmin)
                        </span>
                      ) : adm.role === 'admin' ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-50 text-brand-700 border border-brand-200 dark:bg-brand-500/15 dark:text-brand-300 dark:border-brand-500/30">
                          مدير كتالوج وطلبات (Admin)
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30">
                          مشغل مستودع (Operator)
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      {adm.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
                          نشط (Actif)
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20">
                          معطل (Désactivé)
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 pl-5 text-left">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openEditModal(adm)}
                          className="p-1.5 rounded-lg text-slate-600 hover:text-brand-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-brand-400 dark:hover:bg-slate-800 transition-colors"
                          title="تعديل الحساب"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        {adm.id !== currentUser?.id && (
                          <button
                            onClick={() => toggleAdminStatus(adm)}
                            className={`p-1.5 rounded-lg transition-colors ${
                              adm.is_active
                                ? 'text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:text-rose-400 dark:hover:bg-slate-800'
                                : 'text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:text-emerald-400 dark:hover:bg-slate-800'
                            }`}
                            title={adm.is_active ? 'تعطيل الحساب' : 'تفعيل الحساب'}
                          >
                            {adm.is_active ? (
                              <UserX className="w-4 h-4" />
                            ) : (
                              <UserCheck className="w-4 h-4" />
                            )}
                          </button>
                        )}
                      </div>
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

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/75 backdrop-blur-sm animate-fade-in overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative my-8 transition-colors">
            <h3 className="text-base font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-brand-600 dark:text-brand-400" />
              <span>{editingAdmin ? 'تعديل حساب المشرف' : 'إنشاء حساب مشرف جديد'}</span>
            </h3>

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  الاسم الكامل (Nom & Prénom) *
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="مثال: يوسف حدجاب"
                  required
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  البريد الإلكتروني (Email) *
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@kgp-list.dz"
                  required
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500 text-left dir-ltr"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  كلمة المرور {editingAdmin ? '(اتركها فارغة إذا لم ترغب بتغييرها)' : '*'}
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required={!editingAdmin}
                  minLength={8}
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500 text-left dir-ltr"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  الدور الإداري (Rôle RBAC) *
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as AdminRole)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-xs focus:outline-none focus:border-brand-500"
                >
                  <option value="superadmin">مدير عام (Superadmin) — تحكم كامل ومراقبة</option>
                  <option value="admin">مدير (Admin) — إدارة الكتالوج والأسعار والطلبات</option>
                  <option value="operator">مشغل (Operator) — متابعة وشحن الطلبيات فقط</option>
                </select>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="admin_active"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="admin_active" className="text-xs font-semibold text-slate-700 dark:text-slate-300 cursor-pointer">
                  الحساب نشط ويمكنه تسجيل الدخول
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-lg shadow-brand-900/30 transition-all disabled:opacity-50"
                >
                  {isSubmitting ? 'جاري المعالجة...' : editingAdmin ? 'حفظ التعديلات' : 'إنشاء المشرف'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

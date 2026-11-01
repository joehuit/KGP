import React from 'react';
import {
  BarChart3,
  Boxes,
  FileSpreadsheet,
  FolderTree,
  History,
  LogOut,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Users,
  Wrench,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export type NavTab =
  | 'dashboard'
  | 'categories'
  | 'products'
  | 'import'
  | 'orders'
  | 'customers'
  | 'admins'
  | 'audit'
  | 'settings';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  isOpen,
  onClose,
}) => {
  const { user, isSuperAdmin, isAdmin, logout } = useAuth();

  const navItems: {
    id: NavTab;
    label: string;
    sublabel: string;
    icon: React.ReactNode;
    superadminOnly?: boolean;
    adminOnly?: boolean;
  }[] = [
    {
      id: 'dashboard',
      label: 'الرئيسية',
      sublabel: 'Tableau de bord',
      icon: <BarChart3 className="w-5 h-5" />,
    },
    {
      id: 'categories',
      label: 'التصنيفات والفئات',
      sublabel: 'Catégories',
      icon: <FolderTree className="w-5 h-5" />,
    },
    {
      id: 'products',
      label: 'قطع الغيار',
      sublabel: 'Catalogue pièces',
      icon: <Boxes className="w-5 h-5" />,
    },
    {
      id: 'import',
      label: 'استيراد Excel',
      sublabel: 'Import XLSX',
      icon: <FileSpreadsheet className="w-5 h-5" />,
      adminOnly: true,
    },
    {
      id: 'orders',
      label: 'الطلبات',
      sublabel: 'Commandes',
      icon: <ShoppingCart className="w-5 h-5" />,
    },
    {
      id: 'customers',
      label: 'الزبائن والورشات',
      sublabel: 'Clients & Ateliers',
      icon: <Users className="w-5 h-5" />,
      adminOnly: true,
    },
    {
      id: 'admins',
      label: 'إدارة المشرفين',
      sublabel: 'Utilisateurs & Rôles',
      icon: <ShieldCheck className="w-5 h-5" />,
      superadminOnly: true,
    },
    {
      id: 'audit',
      label: 'سجل العمليات',
      sublabel: 'Journal d’audit',
      icon: <History className="w-5 h-5" />,
      superadminOnly: true,
    },
    {
      id: 'settings',
      label: 'الإعدادات العامة',
      sublabel: 'Paramètres',
      icon: <Settings className="w-5 h-5" />,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 right-0 z-40 h-full w-72 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 flex flex-col transition-all duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Brand Banner */}
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-400 flex items-center justify-center text-white shadow-lg shadow-brand-900/40">
              <Wrench className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-wide text-slate-900 dark:text-white flex items-center gap-1.5">
                KGP LIST
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-brand-500/15 text-brand-600 dark:text-brand-300 border border-brand-500/30">
                  BELFORT
                </span>
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">قطع غيار الهواتف الذكية</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Menu */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map((item) => {
            if (item.superadminOnly && !isSuperAdmin) return null;
            if (item.adminOnly && !isAdmin) return null;
            const active = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectTab(item.id);
                  onClose();
                }}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-right transition-all font-medium ${
                  active
                    ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/30 font-bold'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800/80 dark:hover:text-white'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={active ? 'text-white' : 'text-slate-400'}>{item.icon}</span>
                  <div>
                    <div className="text-sm">{item.label}</div>
                    <div
                      className={`text-[10px] ${
                        active ? 'text-brand-100' : 'text-slate-400 dark:text-slate-500'
                      }`}
                    >
                      {item.sublabel}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Footer with User info & Logout */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80">
          <div className="flex items-center justify-between mb-3">
            <div className="truncate">
              <p className="text-sm font-bold text-slate-900 dark:text-white truncate">{user?.full_name}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email}</p>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded-full font-bold bg-slate-200 text-slate-700 border border-slate-300 dark:bg-slate-800 dark:border-slate-700 dark:text-brand-300">
              {user?.role === 'superadmin'
                ? 'Superadmin'
                : user?.role === 'admin'
                ? 'Admin'
                : 'Operator'}
            </span>
          </div>

          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-rose-600 hover:bg-rose-50 hover:text-rose-700 border border-rose-200 dark:text-rose-400 dark:hover:bg-rose-500/10 dark:hover:text-rose-300 dark:border-rose-500/20 text-sm font-semibold transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>تسجيل الخروج (Déconnexion)</span>
          </button>
        </div>
      </aside>
    </>
  );
};

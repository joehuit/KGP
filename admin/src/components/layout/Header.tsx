import React from 'react';
import { Menu, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ThemeToggle } from '../common/ThemeToggle';
import { NavTab } from './Sidebar';

interface HeaderProps {
  currentTab: NavTab;
  onOpenSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onOpenSidebar }) => {
  const { user } = useAuth();

  const tabTitles: Record<NavTab, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'لوحة القيادة والمؤشرات العامة',
      subtitle: 'متابعة شاملة للمبيعات والمخزون والطلبات الواردة',
    },
    categories: {
      title: 'إدارة التصنيفات والفئات',
      subtitle: 'تنظيم شاشات، بطاريات، لوحات شحن، وفئات الغيار',
    },
    products: {
      title: 'كتالوج قطع الغيار والأسعار',
      subtitle: 'البحث، تعديل الأسعار، ومراقبة المخزون الفعلي',
    },
    import: {
      title: 'استيراد قطع الغيار عبر ملفات Excel',
      subtitle: 'معالجة فورية وتدقيق للأكواد والأسعار قبل التحديث',
    },
    orders: {
      title: 'إدارة وتتبع طلبات الزبائن',
      subtitle: 'معالجة الطلبات، التحديثات اللوجستية، وتفاصيل الفواتير',
    },
    customers: {
      title: 'دليل الزبائن وورشات الصيانة',
      subtitle: 'قاعدة بيانات الورشات، أرقام الهواتف، وسجل المشتريات',
    },
    admins: {
      title: 'إدارة حسابات المشرفين',
      subtitle: 'تعيين الصلاحيات وتأمين وصول الموظفين للنظام',
    },
    audit: {
      title: 'سجلات العمليات والرقابة الأمنية',
      subtitle: 'تتبع تغييرات الأسعار، الحذف، والعمليات الحساسة',
    },
    settings: {
      title: 'إعدادات النظام العامة',
      subtitle: 'معلومات الخادم، الولايات الجزائرية، والعملة المعتمدة',
    },
  };

  const { title, subtitle } = tabTitles[currentTab] || {
    title: 'KGP LIST Admin',
    subtitle: '',
  };

  return (
    <header className="sticky top-0 z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-4 flex items-center justify-between transition-colors duration-200">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSidebar}
          className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800 transition-colors"
          title="فتح القائمة الجانبية"
        >
          <Menu className="w-6 h-6" />
        </button>

        <div>
          <h2 className="text-lg sm:text-xl font-black text-slate-900 dark:text-white">{title}</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">{subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-2.5 sm:gap-3">
        {/* Environment badge */}
        <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
          <span>خادم KGP نشط (Connecté)</span>
        </span>

        {/* Theme mode toggle */}
        <ThemeToggle />

        {/* User profile pill */}
        <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 transition-colors">
          <div className="w-7 h-7 rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/20 dark:text-brand-400 flex items-center justify-center font-bold text-xs">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden sm:block text-right">
            <div className="text-xs font-bold text-slate-800 dark:text-slate-200">{user?.full_name}</div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono capitalize">{user?.role}</div>
          </div>
        </div>
      </div>
    </header>
  );
};

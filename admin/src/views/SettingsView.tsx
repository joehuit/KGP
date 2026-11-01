import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Coins,
  Globe,
  MapPin,
  Moon,
  RefreshCw,
  Server,
  Settings,
  Shield,
  Sun,
} from 'lucide-react';
import { SystemSettings } from '../types';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useToast } from '../components/common/Toast';
import { ThemeToggle } from '../components/common/ThemeToggle';
import { useTheme } from '../context/ThemeContext';

export const SettingsView: React.FC = () => {
  const { showToast } = useToast();
  const { themeMode } = useTheme();
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchSettings = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (err: any) {
      showToast('تعذر تحميل إعدادات النظام: ' + err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  if (isLoading || !settings) {
    return <LoadingSpinner message="جاري استرداد إعدادات الخادم..." />;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm transition-colors">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-brand-600 dark:text-brand-400" />
            <span>إعدادات النظام والتهيئة العامة (Configuration)</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            محددات بيئة التشغيل، مظهر الواجهة، العملة المعتمدة، وقائمة الولايات المدعومة للتوصيل
          </p>
        </div>

        <button
          onClick={fetchSettings}
          className="p-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
          title="تحديث"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Grid Settings Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Appearance & Theme Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 transition-colors">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-50 text-amber-600 border border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20">
              <Sun className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">مظهر اللوحة</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">فاتح، داكن، أو تلقائي</p>
            </div>
          </div>

          <div className="space-y-3 pt-2 border-t border-slate-200 dark:border-slate-800/80">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500 dark:text-slate-400">الوضع النشط:</span>
              <span className="font-bold text-brand-600 dark:text-brand-400">
                {themeMode === 'light' ? 'المظهر الفاتح' : themeMode === 'dark' ? 'المظهر الداكن' : 'تلقائي (حسب النظام)'}
              </span>
            </div>
            <div className="pt-1">
              <ThemeToggle className="w-full justify-center" />
            </div>
          </div>
        </div>

        {/* Server & Environment Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 transition-colors">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-50 text-brand-600 border border-brand-200 dark:bg-brand-500/10 dark:text-brand-400 dark:border-brand-500/20">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">بيئة تشغيل الخادم</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">FastAPI + PostgreSQL</p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs pt-2 border-t border-slate-200 dark:border-slate-800/80">
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">اسم الخدمة:</span>
              <span className="font-bold text-slate-900 dark:text-white">{settings.project_name}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">الإصدار:</span>
              <span className="font-mono text-brand-600 dark:text-brand-400 font-bold">v{settings.version}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">بيئة النشر:</span>
              <span className="font-mono px-2 py-0.5 rounded-md bg-slate-100 text-emerald-700 border border-slate-200 dark:bg-slate-800 dark:text-emerald-400 font-bold dark:border-slate-700">
                {settings.environment}
              </span>
            </div>
          </div>
        </div>

        {/* Currency & Financial Rules */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 transition-colors">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
              <Coins className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">العملة والحسابات</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">المعاملات التجارية في الجزائر</p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs pt-2 border-t border-slate-200 dark:border-slate-800/80">
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">رمز العملة (ISO):</span>
              <span className="font-mono font-bold text-slate-900 dark:text-white">{settings.currency}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">رمز العرض:</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400">{settings.currency_symbol}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">الاسم التجاري:</span>
              <span className="text-slate-700 dark:text-slate-200">{settings.currency_name_ar}</span>
            </div>
          </div>
        </div>

        {/* Security & Token Rules */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 transition-colors">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600 border border-purple-200 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/20">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">أمان الجلسات والرموز</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">سياسات JWT والتشفير</p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs pt-2 border-t border-slate-200 dark:border-slate-800/80">
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">صلاحية جلسة المشرف:</span>
              <span className="font-mono text-slate-900 dark:text-white font-bold">
                {settings.admin_token_expire_minutes / 60} ساعة
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">صلاحية جلسة الزبون:</span>
              <span className="font-mono text-slate-900 dark:text-white font-bold">
                {settings.customer_token_expire_minutes / (60 * 24)} يوم
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">بوابة التحقق SMS:</span>
              <span className="font-mono px-2 py-0.5 rounded-md bg-slate-100 text-cyan-700 border border-slate-200 dark:bg-slate-800 dark:text-cyan-400 font-bold dark:border-slate-700">
                {settings.sms_gateway_provider}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Algerian Wilayas Reference Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 transition-colors">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-brand-600 dark:text-brand-400" />
            <h4 className="text-sm font-bold text-slate-900 dark:text-white">
              قائمة الـ 58 ولاية جزائرية المعتمدة للتوصيل (Wilayas d'Algérie)
            </h4>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200 dark:bg-brand-500/15 dark:text-brand-300 dark:border-brand-500/30 font-bold">
            {settings.supported_wilayas.length} ولاية
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2.5 pt-2 max-h-80 overflow-y-auto">
          {settings.supported_wilayas.map((w) => (
            <div
              key={w.code}
              className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-xs flex items-center justify-between"
            >
              <div className="truncate">
                <div className="font-bold text-slate-900 dark:text-white truncate">{w.name_ar}</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate">{w.name_fr}</div>
              </div>
              <span className="font-mono font-bold text-brand-600 dark:text-brand-400 text-xs px-1.5 py-0.5 rounded bg-slate-200/70 border border-slate-300 dark:bg-slate-900 dark:border-slate-800">
                {w.code}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

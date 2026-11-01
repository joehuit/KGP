import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Coins,
  Globe,
  MapPin,
  RefreshCw,
  Server,
  Settings,
  Shield,
} from 'lucide-react';
import { SystemSettings } from '../types';
import { api } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useToast } from '../components/common/Toast';

export const SettingsView: React.FC = () => {
  const { showToast } = useToast();
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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-brand-400" />
            <span>إعدادات النظام والتهيئة العامة (Configuration)</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            محددات بيئة التشغيل، العملة المعتمدة، وقائمة الولايات المدعومة للتوصيل
          </p>
        </div>

        <button
          onClick={fetchSettings}
          className="p-2.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          title="تحديث"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Grid Settings Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Server & Environment Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">بيئة تشغيل الخادم</h4>
              <p className="text-xs text-slate-400">FastAPI + PostgreSQL</p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs pt-2 border-t border-slate-800/80">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">اسم الخدمة:</span>
              <span className="font-bold text-white">{settings.project_name}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">الإصدار:</span>
              <span className="font-mono text-brand-400 font-bold">v{settings.version}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">بيئة النشر:</span>
              <span className="font-mono px-2 py-0.5 rounded-md bg-slate-800 text-emerald-400 font-bold border border-slate-700">
                {settings.environment}
              </span>
            </div>
          </div>
        </div>

        {/* Currency & Financial Rules */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Coins className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">العملة والحسابات</h4>
              <p className="text-xs text-slate-400">المعاملات التجارية في الجزائر</p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs pt-2 border-t border-slate-800/80">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">رمز العملة (ISO):</span>
              <span className="font-mono font-bold text-white">{settings.currency}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">رمز العرض:</span>
              <span className="font-bold text-emerald-400">{settings.currency_symbol}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">الاسم التجاري:</span>
              <span className="text-slate-200">{settings.currency_name_ar}</span>
            </div>
          </div>
        </div>

        {/* Security & Token Rules */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">أمان الجلسات والرموز</h4>
              <p className="text-xs text-slate-400">سياسات JWT والتشفير</p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs pt-2 border-t border-slate-800/80">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">صلاحية جلسة المشرف:</span>
              <span className="font-mono text-white font-bold">
                {settings.admin_token_expire_minutes / 60} ساعة
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">صلاحية جلسة الزبون:</span>
              <span className="font-mono text-white font-bold">
                {settings.customer_token_expire_minutes / (60 * 24)} يوم
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">بوابة التحقق SMS:</span>
              <span className="font-mono px-2 py-0.5 rounded-md bg-slate-800 text-cyan-400 font-bold border border-slate-700">
                {settings.sms_gateway_provider}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Algerian Wilayas Reference Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-brand-400" />
            <h4 className="text-sm font-bold text-white">
              قائمة الـ 58 ولاية جزائرية المعتمدة للتوصيل (Wilayas d'Algérie)
            </h4>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-brand-500/15 text-brand-300 border border-brand-500/30 font-bold">
            {settings.supported_wilayas.length} ولاية
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2.5 pt-2 max-h-80 overflow-y-auto">
          {settings.supported_wilayas.map((w) => (
            <div
              key={w.code}
              className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs flex items-center justify-between"
            >
              <div className="truncate">
                <div className="font-bold text-white truncate">{w.name_ar}</div>
                <div className="text-[10px] text-slate-400 truncate">{w.name_fr}</div>
              </div>
              <span className="font-mono font-bold text-brand-400 text-xs px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                {w.code}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

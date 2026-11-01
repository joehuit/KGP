import React from 'react';
import { Monitor, Moon, Sun } from 'lucide-react';
import { ThemeMode, useTheme } from '../../context/ThemeContext';

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { themeMode, setThemeMode } = useTheme();

  const options: { id: ThemeMode; label: string; icon: React.ReactNode; tooltip: string }[] = [
    {
      id: 'light',
      label: 'فاتح',
      icon: <Sun className="w-3.5 h-3.5" />,
      tooltip: 'المظهر الفاتح (Light Mode)',
    },
    {
      id: 'dark',
      label: 'داكن',
      icon: <Moon className="w-3.5 h-3.5" />,
      tooltip: 'المظهر الداكن (Dark Mode)',
    },
    {
      id: 'system',
      label: 'تلقائي',
      icon: <Monitor className="w-3.5 h-3.5" />,
      tooltip: 'تلقائي حسب إعدادات الجهاز (System Mode)',
    },
  ];

  return (
    <div
      role="group"
      aria-label="اختيار مظهر الواجهة"
      className={`inline-flex items-center p-0.5 sm:p-1 rounded-xl bg-slate-100 dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 shadow-inner transition-colors ${className}`}
    >
      {options.map((opt) => {
        const isActive = themeMode === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => setThemeMode(opt.id)}
            title={opt.tooltip}
            aria-pressed={isActive}
            className={`flex items-center gap-1.5 px-2 sm:px-2.5 py-1 rounded-lg text-xs font-semibold transition-all duration-150 ${
              isActive
                ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm border border-slate-200/80 dark:border-slate-700/80 font-bold'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-700/40'
            }`}
          >
            {opt.icon}
            <span className="hidden sm:inline text-[11px]">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
};

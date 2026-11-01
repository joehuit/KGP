import React from 'react';
import { PackageOpen } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'لا توجد بيانات حالياً',
  description = 'لم يتم العثور على أي عناصر مطابقة لخيارات البحث أو التصفية الحالية.',
  action,
  icon,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-slate-50/80 dark:bg-slate-900/40 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 transition-colors">
      <div className="p-4 rounded-2xl bg-slate-200/70 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 mb-4">
        {icon || <PackageOpen className="w-10 h-10" />}
      </div>
      <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">{title}</h3>
      <p className="text-sm text-slate-600 dark:text-slate-400 max-w-sm mb-6">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm transition-colors shadow-lg shadow-brand-900/30"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};

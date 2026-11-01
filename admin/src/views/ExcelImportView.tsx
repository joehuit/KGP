import React, { useRef, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  FileUp,
  FolderPlus,
  RefreshCw,
  Upload,
} from 'lucide-react';
import * as XLSX from 'xlsx';
import { ExcelImportCommitSummary, ExcelImportPreviewResponse } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useToast } from '../components/common/Toast';

export const ExcelImportView: React.FC = () => {
  const { canManageCatalog } = useAuth();
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewData, setPreviewData] = useState<ExcelImportPreviewResponse | null>(null);

  // Commit options
  const [createMissingCategories, setCreateMissingCategories] = useState(true);
  const [updateExistingProducts, setUpdateExistingProducts] = useState(false);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [commitSummary, setCommitSummary] = useState<ExcelImportCommitSummary | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        showToast('يرجى اختيار ملف بصيغة Excel (.xlsx)', 'error');
        return;
      }
      setSelectedFile(file);
      setPreviewData(null);
      setCommitSummary(null);
    }
  };

  const handleUploadAndPreview = async () => {
    if (!selectedFile) return;
    setIsPreviewing(true);
    setCommitSummary(null);
    try {
      const preview = await api.previewExcelImport(selectedFile);
      setPreviewData(preview);
      showToast(
        `تم تحليل الملف بنجاح: ${preview.valid_count} سطر صالح، ${preview.invalid_count} أخطاء.`,
        preview.invalid_count > 0 ? 'info' : 'success'
      );
    } catch (err: any) {
      showToast(err.message || 'فشل في تحليل ملف الإكسل.', 'error');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleCommit = async () => {
    if (!previewData) return;
    setIsCommitting(true);
    try {
      const summary = await api.commitExcelImport({
        items: previewData.rows,
        create_missing_categories: createMissingCategories,
        update_existing_products: updateExistingProducts,
      });
      setCommitSummary(summary);
      setIsConfirmModalOpen(false);
      showToast(
        `اكتملت العملية: تم إنشاء ${summary.created} منتج، وتحديث ${summary.updated} منتج.`,
        'success'
      );
    } catch (err: any) {
      showToast(err.message || 'حدث خطأ أثناء حفظ التحديثات.', 'error');
    } finally {
      setIsCommitting(false);
    }
  };

  const downloadSampleTemplate = () => {
    const sampleRows = [
      {
        Code: 'OLED-SAM-A51',
        Désignation: 'Écran OLED Samsung Galaxy A51 (Original)',
        Catégorie: 'Écrans',
        Prix: 14500.0,
        Quantité: 15,
        Description: 'Service Pack Original Samsung',
      },
      {
        Code: 'BAT-IPH-12',
        Désignation: 'Batterie iPhone 12 / 12 Pro',
        Catégorie: 'Batteries',
        Prix: 3500.0,
        Quantité: 20,
        Description: 'Capacité 2815mAh Haute Qualité',
      },
      {
        Code: 'NAP-CHG-REDMI9',
        Désignation: 'Nappe Connecteur de Charge Redmi 9',
        Catégorie: 'Connecteurs',
        Prix: 950.0,
        Quantité: 50,
        Description: 'Avec Microphone et Jack Audio',
      },
    ];

    const worksheet = XLSX.utils.json_to_sheet(sampleRows);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Modèle');
    XLSX.writeFile(workbook, 'kgp_modele_import_pieces.xlsx');
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-brand-400" />
            <span>استيراد وتحديث قطع الغيار عبر Excel (XLSX)</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            رفع ملفات الموردين، التدقيق المسبق للأسعار والموديلات، والكشف عن التكرارات قبل الحفظ النهائي
          </p>
        </div>

        <button
          onClick={downloadSampleTemplate}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-bold transition-colors"
        >
          <Download className="w-4 h-4 text-brand-400" />
          <span>تحميل نموذج Excel المرجعي (Modèle)</span>
        </button>
      </div>

      {/* Step 1: Upload Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <h4 className="text-sm font-bold text-white mb-3">الخطوة 1: اختيار ملف Excel (.xlsx)</h4>
        
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-700 hover:border-brand-500 rounded-2xl p-8 text-center cursor-pointer transition-colors bg-slate-950/40"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".xlsx, .xls"
            className="hidden"
          />
          <div className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-400 flex items-center justify-center mx-auto mb-3">
            <FileUp className="w-6 h-6" />
          </div>
          <p className="text-sm font-bold text-white mb-1">
            {selectedFile ? selectedFile.name : 'انقر لاختيار ملف الإكسل أو قم بسحبه إلى هنا'}
          </p>
          <p className="text-xs text-slate-500">
            الملفات المدعومة: .xlsx (يدعم أسماء الأعمدة بالعربية والفرنسية)
          </p>
        </div>

        {selectedFile && !previewData && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleUploadAndPreview}
              disabled={isPreviewing}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-lg shadow-brand-900/30 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isPreviewing ? 'animate-spin' : ''}`} />
              <span>{isPreviewing ? 'جاري الفحص والمعاينة...' : 'معاينة وتدقيق الملف (Analyser)'}</span>
            </button>
          </div>
        )}
      </div>

      {/* Step 2: Preview & Validation Table */}
      {previewData && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400 font-bold block mb-1">إجمالي الأسطر</span>
              <span className="text-2xl font-black text-white">{previewData.total_rows}</span>
            </div>
            <div className="bg-slate-900 border border-emerald-500/20 rounded-xl p-4">
              <span className="text-xs text-emerald-400 font-bold block mb-1">أسطر صالحة للاستيراد</span>
              <span className="text-2xl font-black text-emerald-400">{previewData.valid_count}</span>
            </div>
            <div className="bg-slate-900 border border-rose-500/20 rounded-xl p-4">
              <span className="text-xs text-rose-400 font-bold block mb-1">أسطر تحتوي أخطاء</span>
              <span className="text-2xl font-black text-rose-400">{previewData.invalid_count}</span>
            </div>
            <div className="bg-slate-900 border border-cyan-500/20 rounded-xl p-4">
              <span className="text-xs text-cyan-400 font-bold block mb-1">قطع جديدة / للتحديث</span>
              <span className="text-sm font-bold text-white block mt-1">
                جديد: {previewData.new_products_count} | تحديث: {previewData.update_products_count}
              </span>
            </div>
          </div>

          {/* New categories notice */}
          {previewData.new_categories.length > 0 && (
            <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderPlus className="w-5 h-5 text-cyan-400 shrink-0" />
                <span>
                  تم اكتشاف فئات جديدة سيتم إنشاؤها تلقائياً عند التأكيد:{' '}
                  <strong>{previewData.new_categories.join(', ')}</strong>
                </span>
              </div>
            </div>
          )}

          {/* Table Preview */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h4 className="text-sm font-bold text-white">معاينة تفاصيل البيانات المدققة</h4>
              <span className="text-xs text-slate-400 font-mono">
                {previewData.filename}
              </span>
            </div>

            <div className="max-h-96 overflow-y-auto overflow-x-auto">
              <table className="w-full text-right text-xs">
                <thead className="sticky top-0 bg-slate-950 border-b border-slate-800 text-slate-400">
                  <tr>
                    <th className="py-2.5 pr-4 font-bold">السطر</th>
                    <th className="py-2.5 px-3 font-bold">كود القطعة (SKU)</th>
                    <th className="py-2.5 px-3 font-bold">اسم القطعة</th>
                    <th className="py-2.5 px-3 font-bold">الفئة</th>
                    <th className="py-2.5 px-3 font-bold">السعر (DZD)</th>
                    <th className="py-2.5 px-3 font-bold">المخزون</th>
                    <th className="py-2.5 pl-4 font-bold text-left">حالة الفحص</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {previewData.rows.map((row) => (
                    <tr
                      key={row.row_index}
                      className={`hover:bg-slate-800/30 ${
                        row.status === 'invalid'
                          ? 'bg-rose-500/5'
                          : row.status === 'update'
                          ? 'bg-amber-500/5'
                          : ''
                      }`}
                    >
                      <td className="py-2.5 pr-4 font-mono text-slate-500 font-bold">
                        #{row.row_index}
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-white">
                        {row.sku || <span className="text-rose-400">مفقود</span>}
                      </td>
                      <td className="py-2.5 px-3 text-slate-200">
                        {row.name}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {row.category_name}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-emerald-400 font-bold">
                        {row.selling_price} د.ج
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {row.available_quantity ?? 'غير محدد'}
                      </td>
                      <td className="py-2.5 pl-4 text-left">
                        {row.status === 'invalid' ? (
                          <div className="flex flex-col items-start gap-1">
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                              <AlertCircle className="w-3 h-3" />
                              <span>غير صالح</span>
                            </span>
                            <span className="text-[10px] text-rose-400 leading-tight">
                              {row.errors.join(' | ')}
                            </span>
                          </div>
                        ) : row.status === 'update' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            <span>منتج موجود مسبقاً (تحديث)</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>جديد صالح</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Step 3: Explicit Options & Commit Button */}
          {canManageCatalog && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
              <h4 className="text-sm font-bold text-white">الخطوة 2: خيارات وتأكيد الاستيراد</h4>
              
              <div className="space-y-3">
                <label className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={createMissingCategories}
                    onChange={(e) => setCreateMissingCategories(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-brand-600 focus:ring-brand-500"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">
                      إنشاء الفئات غير الموجودة تلقائياً (Création automatique des catégories)
                    </div>
                    <div className="text-[11px] text-slate-400">
                      سيتم فتح فئات جديدة للقطع التي تحمل أسماء فئات غير مسجلة حالياً
                    </div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={updateExistingProducts}
                    onChange={(e) => setUpdateExistingProducts(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-brand-600 focus:ring-brand-500"
                  />
                  <div>
                    <div className="text-xs font-bold text-white">
                      تحديث أسعار ومخزون المنتجات الموجودة مسبقاً (Mise à jour des prix/stock existants)
                    </div>
                    <div className="text-[11px] text-slate-400">
                      إذا تم إلغاء التحديد، سيتم تجاوز المنتجات ذات الأكواد المكررة وتجاهلها لحماية البيانات الحالية
                    </div>
                  </div>
                </label>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setIsConfirmModalOpen(true)}
                  disabled={previewData.valid_count === 0}
                  className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-900/30 transition-all disabled:opacity-50"
                >
                  تأكيد وحفظ الاستيراد في قاعدة البيانات (Confirmer l'import)
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Commit Result Summary Banner */}
      {commitSummary && (
        <div className="bg-slate-900 border border-emerald-500/40 rounded-2xl p-6 shadow-2xl animate-fade-in space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                تم استيراد وحفظ قطع الغيار بنجاح في قاعدة البيانات!
              </h3>
              <p className="text-xs text-slate-400">
                الملخص النهائي للمعالجة المحاسبية والكتالوج:
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block mb-1">قطع جديدة تم إنشاؤها</span>
              <span className="text-xl font-bold text-emerald-400">{commitSummary.created}</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block mb-1">قطع تم تحديث أسعارها/مخزونها</span>
              <span className="text-xl font-bold text-brand-400">{commitSummary.updated}</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block mb-1">أسطر تم تجاوزها</span>
              <span className="text-xl font-bold text-amber-400">{commitSummary.skipped}</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block mb-1">أسطر فاشلة</span>
              <span className="text-xl font-bold text-rose-400">{commitSummary.failed}</span>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Dialog */}
      <ConfirmModal
        isOpen={isConfirmModalOpen}
        title="تأكيد حفظ التحديثات في الكتالوج"
        message={`أنت على وشك معالجة ${previewData?.valid_count} سطر في الكتالوج. هل تود بالتأكيد حفظ التعديلات وإدراج البيانات في قاعدة بيانات KGP LIST؟`}
        confirmLabel="نعم، قم بالحفظ الآن"
        cancelLabel="مراجعة الملف"
        isDestructive={false}
        isLoading={isCommitting}
        onConfirm={handleCommit}
        onCancel={() => setIsConfirmModalOpen(false)}
      />
    </div>
  );
};

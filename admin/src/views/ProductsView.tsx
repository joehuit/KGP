import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Boxes,
  CheckCircle,
  Edit2,
  Filter,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from 'lucide-react';
import { Category, Product } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Pagination } from '../components/common/Pagination';
import { useToast } from '../components/common/Toast';

export const ProductsView: React.FC = () => {
  const { canManageCatalog } = useAuth();
  const { showToast } = useToast();

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters & Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<number | undefined>(undefined);
  const [activeOnly, setActiveOnly] = useState<boolean>(false);

  // Create / Edit Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [sku, setSku] = useState('');
  const [name, setName] = useState('');
  const [categoryId, setCategoryId] = useState<number>(1);
  const [sellingPrice, setSellingPrice] = useState<string>('0.00');
  const [availableQuantity, setAvailableQuantity] = useState<string>('0');
  const [description, setDescription] = useState<string>('');
  const [isActive, setIsActive] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Delete / Deactivate State
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchCategories = async () => {
    try {
      const cats = await api.listCategories(false);
      setCategories(cats);
      if (cats.length > 0 && !categoryId) {
        setCategoryId(cats[0].id);
      }
    } catch {
      // Ignore
    }
  };

  const fetchProducts = async () => {
    setIsLoading(true);
    try {
      const res = await api.listProducts({
        page,
        page_size: pageSize,
        category_id: selectedCategory,
        search: searchTerm.trim() || undefined,
        active_only: activeOnly,
      });
      setProducts(res.items);
      setTotalPages(res.meta.total_pages);
      setTotalItems(res.meta.total_items);
    } catch (err: any) {
      showToast('تعذر تحميل كتالوج قطع الغيار: ' + err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [page, selectedCategory, activeOnly]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  const openCreateModal = () => {
    setEditingProduct(null);
    setSku('');
    setName('');
    if (categories.length > 0) setCategoryId(categories[0].id);
    setSellingPrice('0.00');
    setAvailableQuantity('10');
    setDescription('');
    setIsActive(true);
    setIsModalOpen(true);
  };

  const openEditModal = (prod: Product) => {
    setEditingProduct(prod);
    setSku(prod.sku);
    setName(prod.name);
    setCategoryId(prod.category_id);
    setSellingPrice(prod.selling_price.toString());
    setAvailableQuantity(prod.available_quantity !== null ? prod.available_quantity.toString() : '');
    setDescription(prod.description || '');
    setIsActive(prod.is_active);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sku.trim() || !name.trim()) {
      showToast('الرمز والاسم مطلوبان.', 'error');
      return;
    }

    const priceNum = parseFloat(sellingPrice);
    if (isNaN(priceNum) || priceNum < 0) {
      showToast('سعر البيع يجب أن يكون رقماً موجباً.', 'error');
      return;
    }

    const qtyVal = availableQuantity.trim() === '' ? null : parseInt(availableQuantity);
    if (qtyVal !== null && (isNaN(qtyVal) || qtyVal < 0)) {
      showToast('الكمية يجب أن تكون عدداً صحيحاً أو فارغة.', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      if (editingProduct) {
        await api.updateProduct(editingProduct.id, {
          sku: sku.trim().toUpperCase(),
          name: name.trim(),
          category_id: categoryId,
          selling_price: priceNum.toFixed(2),
          available_quantity: qtyVal,
          description: description.trim() || null,
          is_active: isActive,
        });
        showToast('تم تحديث بيانات القطعة بنجاح.', 'success');
      } else {
        await api.createProduct({
          sku: sku.trim().toUpperCase(),
          name: name.trim(),
          category_id: categoryId,
          selling_price: priceNum.toFixed(2),
          available_quantity: qtyVal,
          description: description.trim() || null,
          is_active: isActive,
        });
        showToast('تمت إضافة القطعة بنجاح إلى الكتالوج.', 'success');
      }
      setIsModalOpen(false);
      fetchProducts();
    } catch (err: any) {
      showToast(err.message || 'فشلت عملية حفظ المنتج.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      const res = await api.deleteProduct(deleteTarget.id);
      showToast(res.message, 'success');
      setDeleteTarget(null);
      fetchProducts();
    } catch (err: any) {
      showToast(err.message || 'تعذر حذف القطعة.', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  const formatPrice = (val: string | number) => {
    const num = typeof val === 'number' ? val : parseFloat(val);
    return isNaN(num) ? '0.00' : num.toLocaleString('fr-DZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className="space-y-6">
      {/* Top Action & Search Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 transition-colors">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Boxes className="w-5 h-5 text-brand-600 dark:text-brand-400" />
              <span>كتالوج قطع الغيار والأسعار (Pièces détachées)</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              قائمة الشاشات والبطاريات وقطع الغيار مع كود SKU، المخزون، والأسعار بالدينار الجزائري
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={fetchProducts}
              className="p-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
              title="تحديث"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>

            {canManageCatalog && (
              <button
                onClick={openCreateModal}
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-lg shadow-brand-900/30 transition-all flex-1 sm:flex-none"
              >
                <Plus className="w-4 h-4" />
                <span>إضافة قطعة جديدة (Ajouter pièce)</span>
              </button>
            )}
          </div>
        </div>

        {/* Filters Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3 pt-2 border-t border-slate-200 dark:border-slate-800/80">
          {/* Search Input */}
          <form onSubmit={handleSearchSubmit} className="sm:col-span-2 relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="ابحث بكود القطعة SKU أو اسم الموديل (مثال: OLED A51)..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500"
            />
            <button
              type="submit"
              className="absolute left-2.5 top-2.5 text-slate-400 hover:text-slate-700 dark:hover:text-white"
            >
              <Search className="w-4 h-4" />
            </button>
          </form>

          {/* Category Filter */}
          <div>
            <select
              value={selectedCategory || ''}
              onChange={(e) => {
                setSelectedCategory(e.target.value ? parseInt(e.target.value) : undefined);
                setPage(1);
              }}
              className="w-full px-3 py-2.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-xs focus:outline-none focus:border-brand-500"
            >
              <option value="">جميع الفئات والتصنيفات</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Active status filter */}
          <div className="flex items-center gap-2 px-3 py-2 bg-slate-100/60 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700/60">
            <input
              type="checkbox"
              id="active_filter"
              checked={activeOnly}
              onChange={(e) => {
                setActiveOnly(e.target.checked);
                setPage(1);
              }}
              className="w-4 h-4 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-brand-600 focus:ring-brand-500"
            />
            <label htmlFor="active_filter" className="text-xs text-slate-700 dark:text-slate-300 font-medium cursor-pointer">
              القطع المفعلة فقط
            </label>
          </div>
        </div>
      </div>

      {/* Products Table */}
      {isLoading ? (
        <LoadingSpinner message="جاري استرجاع قطع الغيار والأسعار..." />
      ) : products.length === 0 ? (
        <EmptyState
          title="لم يتم العثور على قطع غيار"
          description="جرب تغيير معايير البحث أو تصفية الفئة، أو أضف منتجات جديدة."
          action={canManageCatalog ? { label: 'إضافة قطعة غيار', onClick: openCreateModal } : undefined}
          icon={<Boxes className="w-10 h-10" />}
        />
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm transition-colors">
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                  <th className="py-3.5 pr-5 font-bold">كود القطعة (SKU)</th>
                  <th className="py-3.5 px-4 font-bold">اسم القطعة والموديل</th>
                  <th className="py-3.5 px-4 font-bold">سعر البيع (DZD)</th>
                  <th className="py-3.5 px-4 font-bold">المخزون (Stock)</th>
                  <th className="py-3.5 px-4 font-bold">الحالة</th>
                  <th className="py-3.5 pl-5 font-bold text-left">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/60 font-medium">
                {products.map((prod) => (
                  <tr key={prod.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 pr-5 font-mono text-brand-600 dark:text-brand-400 font-bold">
                      {prod.sku}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="text-slate-900 dark:text-white font-bold text-sm">{prod.name}</div>
                      {prod.description && (
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-xs">
                          {prod.description}
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-bold text-emerald-600 dark:text-emerald-400 text-sm">
                      {formatPrice(prod.selling_price)}{' '}
                      <span className="text-[10px] text-slate-500 dark:text-slate-400">د.ج</span>
                    </td>
                    <td className="py-3.5 px-4">
                      {prod.available_quantity === null ? (
                        <span className="text-slate-400 dark:text-slate-500 font-mono">غير محدد</span>
                      ) : prod.available_quantity <= 5 ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30">
                          {prod.available_quantity} قطع (منخفض)
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700">
                          {prod.available_quantity} قطع
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      {prod.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
                          معروض (Actif)
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700">
                          مخفي (Inactif)
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 pl-5 text-left">
                      {canManageCatalog ? (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openEditModal(prod)}
                            className="p-1.5 rounded-lg text-slate-600 hover:text-brand-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-brand-400 dark:hover:bg-slate-800 transition-colors"
                            title="تعديل القطعة"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeleteTarget(prod)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:text-slate-400 dark:hover:text-rose-400 dark:hover:bg-slate-800 transition-colors"
                            title="حذف أو تعطيل القطعة"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <span className="text-slate-400 dark:text-slate-500 text-[11px]">للقراءة فقط</span>
                      )}
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
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative my-8 transition-colors">
            <h3 className="text-base font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <Boxes className="w-5 h-5 text-brand-600 dark:text-brand-400" />
              <span>{editingProduct ? 'تعديل قطعة غيار' : 'إضافة قطعة غيار جديدة'}</span>
            </h3>

            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    كود القطعة الفريد (SKU) *
                  </label>
                  <input
                    type="text"
                    value={sku}
                    onChange={(e) => setSku(e.target.value.toUpperCase())}
                    placeholder="مثال: OLED-SAM-A51"
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500 font-mono uppercase"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    الفئة والتصنيف *
                  </label>
                  <select
                    value={categoryId}
                    onChange={(e) => setCategoryId(parseInt(e.target.value))}
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-xs focus:outline-none focus:border-brand-500"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  اسم القطعة والموديل التجاري *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="مثال: Écran OLED Samsung Galaxy A51 (Original Service Pack)"
                  required
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    سعر البيع بالدينار الجزائري (DZD) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={sellingPrice}
                    onChange={(e) => setSellingPrice(e.target.value)}
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-xs focus:outline-none focus:border-brand-500 font-mono font-bold text-emerald-600 dark:text-emerald-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    الكمية المتوفرة بالمخزون (Stock)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={availableQuantity}
                    onChange={(e) => setAvailableQuantity(e.target.value)}
                    placeholder="فارغ للكمية غير المحددة"
                    className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-xs focus:outline-none focus:border-brand-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  ملاحظات أو مواصفات تقنية (Description)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="درجة الجودة، المورد، التوافق، نوع الشاشة..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-xs focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="prod_active"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="prod_active" className="text-xs font-semibold text-slate-700 dark:text-slate-300 cursor-pointer">
                  تفعيل ظهور القطعة في تطبيق الزبائن
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
                  {isSubmitting ? 'جاري الحفظ...' : editingProduct ? 'حفظ التعديلات' : 'إضافة القطعة'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={!!deleteTarget}
        title="تأكيد حذف / تعطيل القطعة"
        message={`هل أنت متأكد من رغبتك في حذف قطعة "${deleteTarget?.name}" (كود: ${deleteTarget?.sku})؟ إذا كانت القطعة قد طلبت سابقاً في فواتير قديمة، فسيتم تعطيلها تلقائياً بدلاً من حذفها للحفاظ على سجلات البيع.`}
        confirmLabel="تأكيد العملية"
        cancelLabel="تراجع"
        isDestructive={true}
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
};

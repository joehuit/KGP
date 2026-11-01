import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './components/common/Toast';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { AppLayout } from './components/layout/AppLayout';
import { NavTab } from './components/layout/Sidebar';
import { LoginView } from './views/LoginView';
import { DashboardView } from './views/DashboardView';
import { CategoriesView } from './views/CategoriesView';
import { ProductsView } from './views/ProductsView';
import { ExcelImportView } from './views/ExcelImportView';
import { OrdersView } from './views/OrdersView';
import { CustomersView } from './views/CustomersView';
import { AdminUsersView } from './views/AdminUsersView';
import { AuditLogsView } from './views/AuditLogsView';
import { SettingsView } from './views/SettingsView';

const MainApp: React.FC = () => {
  const { isAuthenticated, isLoading, isSuperAdmin, isAdmin } = useAuth();
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <LoadingSpinner message="جاري الاتصال بنظام KGP LIST..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  // Route protection for superadmin views
  if ((currentTab === 'admins' || currentTab === 'audit') && !isSuperAdmin) {
    setCurrentTab('dashboard');
  }

  // Route protection for admin-only views (customers, import)
  if ((currentTab === 'customers' || currentTab === 'import') && !isAdmin) {
    setCurrentTab('dashboard');
  }

  const renderActiveView = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardView onNavigate={(tab) => setCurrentTab(tab)} />;
      case 'categories':
        return <CategoriesView />;
      case 'products':
        return <ProductsView />;
      case 'import':
        return <ExcelImportView />;
      case 'orders':
        return <OrdersView />;
      case 'customers':
        return <CustomersView />;
      case 'admins':
        return <AdminUsersView />;
      case 'audit':
        return <AuditLogsView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <DashboardView onNavigate={(tab) => setCurrentTab(tab)} />;
    }
  };

  return (
    <AppLayout currentTab={currentTab} onSelectTab={(tab) => setCurrentTab(tab)}>
      {renderActiveView()}
    </AppLayout>
  );
};

export const App: React.FC = () => {
  return (
    <ToastProvider>
      <AuthProvider>
        <MainApp />
      </AuthProvider>
    </ToastProvider>
  );
};

export default App;

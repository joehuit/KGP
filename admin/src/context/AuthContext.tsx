import React, { createContext, useContext, useEffect, useState } from 'react';
import { AdminRole, AdminUser } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: AdminUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isSuperAdmin: boolean;
  isAdmin: boolean;
  isOperator: boolean;
  canManageCatalog: boolean;
  canManageUsers: boolean;
  canUpdateOrders: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AdminUser | null>(() => {
    const saved = localStorage.getItem('kgp_admin_profile');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('kgp_admin_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Sync / refresh profile on boot
  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('kgp_admin_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const profile = await api.getProfile();
        setUser(profile);
        localStorage.setItem('kgp_admin_profile', JSON.stringify(profile));
      } catch (err) {
        setUser(null);
        setToken(null);
        localStorage.removeItem('kgp_admin_token');
        localStorage.removeItem('kgp_admin_profile');
      } finally {
        setIsLoading(false);
      }
    };

    verifyToken();

    // Listen to unauthorized event
    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.login({ email, password });
    localStorage.setItem('kgp_admin_token', res.access_token);
    setToken(res.access_token);

    const profile: AdminUser = {
      id: res.user_id,
      email,
      full_name: res.full_name,
      role: res.role,
      is_active: true,
      permissions: res.permissions,
    };
    localStorage.setItem('kgp_admin_profile', JSON.stringify(profile));
    setUser(profile);
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch {
      // Local clean regardless
    } finally {
      setUser(null);
      setToken(null);
    }
  };

  const role = user?.role;
  const isSuperAdmin = role === 'superadmin';
  const isAdmin = role === 'admin' || isSuperAdmin;
  const isOperator = role === 'operator' || isAdmin;

  const canManageCatalog = isSuperAdmin || role === 'admin';
  const canManageUsers = isSuperAdmin;
  const canUpdateOrders = isSuperAdmin || role === 'admin' || role === 'operator';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        logout,
        isSuperAdmin,
        isAdmin,
        isOperator,
        canManageCatalog,
        canManageUsers,
        canUpdateOrders,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};

import React from 'react';
import { OrderStatus } from '../../types';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral' | 'info';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'neutral', className = '' }) => {
  const variantStyles = {
    primary: 'bg-brand-500/15 text-brand-400 border-brand-500/30',
    success: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    neutral: 'bg-slate-800 text-slate-300 border-slate-700',
    info: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};

export const OrderStatusBadge: React.FC<{ status: OrderStatus }> = ({ status }) => {
  switch (status) {
    case 'PENDING':
      return <Badge variant="warning">قيد الانتظار (En attente)</Badge>;
    case 'CONFIRMED':
      return <Badge variant="primary">مؤكد (Confirmé)</Badge>;
    case 'PROCESSING':
      return <Badge variant="info">قيد التحضير (En préparation)</Badge>;
    case 'SHIPPED':
      return <Badge variant="info">تم الشحن (Expédié)</Badge>;
    case 'DELIVERED':
      return <Badge variant="success">تم التسليم (Livré)</Badge>;
    case 'CANCELLED':
      return <Badge variant="danger">ملغى (Annulé)</Badge>;
    default:
      return <Badge>{status}</Badge>;
  }
};

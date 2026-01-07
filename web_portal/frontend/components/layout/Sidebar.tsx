'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Car,
  Database,
  GitBranch,
  Upload,
  TrendingUp,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Fast Moving Vehicles', href: '/dashboard/vehicles/fast-moving', icon: Car },
  { name: 'Scraped Vehicles', href: '/dashboard/vehicles/scraped', icon: Database, adminOnly: true },
  { name: 'ERP Mapping', href: '/dashboard/mapping', icon: GitBranch, adminOnly: true },
  { name: 'Bulk Upload', href: '/dashboard/bulk-upload', icon: Upload, adminOnly: true },
  { name: 'Price Analytics', href: '/dashboard/analytics', icon: TrendingUp },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const filteredNavItems = navItems.filter(
    (item) => !item.adminOnly || user?.role === 'admin'
  );

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white w-64">
      {/* Logo/Title */}
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-2xl font-bold">CDB Vehicle Portal</h1>
        <p className="text-sm text-gray-400 mt-1">
          {user?.username} ({user?.role})
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {filteredNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )}
            >
              <Icon className="h-5 w-5" />
              <span className="font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-gray-700">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors w-full"
        >
          <LogOut className="h-5 w-5" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
};

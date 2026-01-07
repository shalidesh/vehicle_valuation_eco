'use client';

import { useEffect, useState } from 'react';
import { analyticsAPI } from '@/lib/api';
import { DashboardStats } from '@/types';
import { Car, Database, GitBranch, Users, TrendingUp } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await analyticsAPI.getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Fast Moving Vehicles',
      value: stats?.total_fast_moving || 0,
      icon: Car,
      color: 'bg-blue-500',
    },
    {
      title: 'Scraped Vehicles',
      value: stats?.total_scraped || 0,
      icon: Database,
      color: 'bg-green-500',
    },
    {
      title: 'ERP Mappings',
      value: stats?.total_mappings || 0,
      icon: GitBranch,
      color: 'bg-purple-500',
    },
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'bg-orange-500',
    },
    {
      title: 'Recent Updates (7 days)',
      value: stats?.recent_updates_count || 0,
      icon: TrendingUp,
      color: 'bg-pink-500',
    },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.title}
              className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{card.value}</p>
                </div>
                <div className={`${card.color} p-3 rounded-lg`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Welcome to CDB Vehicle Portal</h2>
        <p className="text-gray-600 mb-4">
          This portal allows you to manage vehicle data with the following features:
        </p>
        <ul className="list-disc list-inside space-y-2 text-gray-700">
          <li>Manage fast-moving vehicle inventory</li>
          <li>View and update scraped vehicle data (Admin only)</li>
          <li>Configure ERP model name mappings (Admin only)</li>
          <li>Analyze vehicle price movements and trends</li>
          <li>Track all changes with comprehensive audit logging</li>
        </ul>
      </div>
    </div>
  );
}

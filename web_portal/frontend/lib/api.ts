import axios, { AxiosError } from 'axios';
import type {
  User,
  LoginCredentials,
  AuthTokens,
  FastMovingVehicle,
  FastMovingVehicleCreate,
  FastMovingVehicleUpdate,
  ScrapedVehicle,
  ScrapedVehicleCreate,
  ScrapedVehicleUpdate,
  ERPModelMapping,
  ERPModelMappingCreate,
  ERPModelMappingUpdate,
  DashboardStats,
  PriceMovement,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper functions for safe localStorage access
const getLocalStorage = (key: string): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(key);
};

const setLocalStorage = (key: string, value: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(key, value);
};

const removeLocalStorage = (key: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(key);
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getLocalStorage('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getLocalStorage('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = response.data;

          setLocalStorage('access_token', access_token);
          setLocalStorage('refresh_token', refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        removeLocalStorage('access_token');
        removeLocalStorage('refresh_token');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Authentication APIs
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const response = await api.post('/api/auth/login', credentials);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  logout: () => {
    removeLocalStorage('access_token');
    removeLocalStorage('refresh_token');
  },
};

// Fast Moving Vehicles APIs
export const fastMovingVehiclesAPI = {
  getAll: async (params?: {
    vehicle_type?: string;
    manufacturer?: string;
    model?: string;
    yom?: number;
    skip?: number;
    limit?: number;
  }): Promise<FastMovingVehicle[]> => {
    const response = await api.get('/api/vehicles/fast-moving', { params });
    return response.data;
  },

  create: async (vehicle: FastMovingVehicleCreate): Promise<FastMovingVehicle> => {
    const response = await api.post('/api/vehicles/fast-moving', vehicle);
    return response.data;
  },

  update: async (id: number, vehicle: FastMovingVehicleUpdate): Promise<FastMovingVehicle> => {
    const response = await api.put(`/api/vehicles/fast-moving/${id}`, vehicle);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/vehicles/fast-moving/${id}`);
  },
};

// Scraped Vehicles APIs
export const scrapedVehiclesAPI = {
  getAll: async (params?: {
    vehicle_type?: string;
    manufacturer?: string;
    model?: string;
    yom?: number;
    skip?: number;
    limit?: number;
  }): Promise<ScrapedVehicle[]> => {
    const response = await api.get('/api/vehicles/scraped', { params });
    return response.data;
  },

  create: async (vehicle: ScrapedVehicleCreate): Promise<ScrapedVehicle> => {
    const response = await api.post('/api/vehicles/scraped', vehicle);
    return response.data;
  },

  update: async (id: number, vehicle: ScrapedVehicleUpdate): Promise<ScrapedVehicle> => {
    const response = await api.put(`/api/vehicles/scraped/${id}`, vehicle);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/vehicles/scraped/${id}`);
  },
};

// ERP Model Mapping APIs
export const erpMappingAPI = {
  getAll: async (params?: {
    manufacturer?: string;
    erp_name?: string;
    mapped_name?: string;
    skip?: number;
    limit?: number;
  }): Promise<ERPModelMapping[]> => {
    const response = await api.get('/api/mapping', { params });
    return response.data;
  },

  create: async (mapping: ERPModelMappingCreate): Promise<ERPModelMapping> => {
    const response = await api.post('/api/mapping', mapping);
    return response.data;
  },

  update: async (id: number, mapping: ERPModelMappingUpdate): Promise<ERPModelMapping> => {
    const response = await api.put(`/api/mapping/${id}`, mapping);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/mapping/${id}`);
  },
};

// Analytics APIs
export const analyticsAPI = {
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/api/analytics/dashboard-stats');
    return response.data;
  },

  getPriceMovement: async (
    manufacturer: string,
    model: string,
    yom: number,
    days: number = 90,
    data_source: string = 'fast_moving',
    vehicle_type?: string
  ): Promise<PriceMovement> => {
    const response = await api.get('/api/analytics/price-movement', {
      params: { manufacturer, model, yom, days, data_source, vehicle_type },
    });
    return response.data;
  },

  getFastMovingIndex: async (
    days: number = 90,
    data_source: string = 'fast_moving',
    vehicle_type?: string,
    selectedModels?: any[]
  ): Promise<PriceMovement> => {
    const response = await api.post('/api/analytics/fast-moving-index', {
      days,
      data_source,
      vehicle_type,
      models: selectedModels || [],
    });
    return response.data;
  },

  getAllModelYears: async (data_source: string = 'fast_moving', vehicle_type?: string): Promise<any[]> => {
    const response = await api.get('/api/analytics/all-model-years', {
      params: { data_source, vehicle_type },
    });
    return response.data;
  },

  getManufacturers: async (data_source: string = 'fast_moving', vehicle_type?: string): Promise<string[]> => {
    const response = await api.get('/api/analytics/manufacturers', {
      params: { data_source, vehicle_type },
    });
    return response.data;
  },

  getModels: async (manufacturer?: string, data_source: string = 'fast_moving', vehicle_type?: string): Promise<string[]> => {
    const response = await api.get('/api/analytics/models', {
      params: { manufacturer, data_source, vehicle_type },
    });
    return response.data;
  },

  getYears: async (manufacturer?: string, model?: string, data_source: string = 'fast_moving', vehicle_type?: string): Promise<number[]> => {
    const response = await api.get('/api/analytics/years', {
      params: { manufacturer, model, data_source, vehicle_type },
    });
    return response.data;
  },
};

// Bulk Upload APIs
export const bulkUploadAPI = {
  uploadCSV: async (tableName: string, data: any[]) => {
    const response = await api.post('/api/bulk-upload', {
      table_name: tableName,
      data: data,
    });
    return response;
  },
};

export default api;

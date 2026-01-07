export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'manager';
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface FastMovingVehicle {
  id: number;
  type: string;  // Registered or Unregistered
  manufacturer: string;
  model: string;
  yom: number;
  price: number | null;
  date: string;  // User-specified date when price was recorded
  updated_date: string;
  updated_by: number | null;
}

export interface FastMovingVehicleCreate {
  type: string;  // Registered or Unregistered
  manufacturer: string;
  model: string;
  yom: number;
  price?: number | null;
  date: string;  // User-specified date when price was recorded
}

export interface FastMovingVehicleUpdate {
  type?: string;  // Registered or Unregistered
  manufacturer?: string;
  model?: string;
  yom?: number;
  price?: number | null;
  date?: string;  // User-specified date when price was recorded
}

export interface ScrapedVehicle {
  id: number;
  type: string;  // Registered or Unregistered
  manufacturer: string;
  model: string;
  yom: number;
  transmission: string | null;
  fuel_type: string | null;
  mileage: number | null;
  price: number | null;
  updated_date: string;
}

export interface ScrapedVehicleCreate {
  type: string;  // Registered or Unregistered
  manufacturer: string;
  model: string;
  yom: number;
  transmission?: string | null;
  fuel_type?: string | null;
  mileage?: number | null;
  price?: number | null;
}

export interface ScrapedVehicleUpdate {
  type?: string;  // Registered or Unregistered
  manufacturer?: string;
  model?: string;
  yom?: number;
  transmission?: string | null;
  fuel_type?: string | null;
  mileage?: number | null;
  price?: number | null;
}

export interface ERPModelMapping {
  id: number;
  manufacturer: string;
  erp_name: string;
  mapped_name: string;
  updated_date: string;
  updated_by: number | null;
}

export interface ERPModelMappingCreate {
  manufacturer: string;
  erp_name: string;
  mapped_name: string;
}

export interface ERPModelMappingUpdate {
  manufacturer?: string;
  erp_name?: string;
  mapped_name?: string;
}

export interface DashboardStats {
  total_fast_moving: number;
  total_scraped: number;
  total_mappings: number;
  recent_updates_count: number;
  total_users: number;
}

export interface PricePoint {
  date: string;
  price: number;
}

export interface PriceMovement {
  manufacturer: string;
  model: string;
  yom: number;
  price_history: PricePoint[];
  avg_price: number | null;
  min_price: number | null;
  max_price: number | null;
  trend: 'increasing' | 'decreasing' | 'stable' | null;
}

export interface ModelYearOption {
  manufacturer: string;
  model: string;
  year: number;
  label: string;
}

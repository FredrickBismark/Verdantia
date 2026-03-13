import type { ApiListResponse, ApiResponse, SoilTest } from '../types';
import { api } from './client';

export interface SoilTestCreate {
  location?: string | null;
  test_date: string;
  ph?: number | null;
  nitrogen_ppm?: number | null;
  phosphorus_ppm?: number | null;
  potassium_ppm?: number | null;
  organic_matter_pct?: number | null;
  texture?: string | null;
  notes?: string | null;
}

export const soilApi = {
  list: (gardenId: number, skip = 0, limit = 20) =>
    api.get<ApiListResponse<SoilTest>>(
      `/gardens/${gardenId}/soil-tests?skip=${skip}&limit=${limit}`,
    ),

  create: (gardenId: number, data: SoilTestCreate) =>
    api.post<ApiResponse<SoilTest>>(`/gardens/${gardenId}/soil-tests`, data),
};

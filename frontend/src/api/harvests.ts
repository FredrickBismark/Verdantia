import type { ApiListResponse, ApiResponse, HarvestLog } from '../types';
import { api } from './client';

export interface HarvestCreate {
  harvest_date: string;
  quantity: number;
  unit: string;
  quality_rating: number | null;
  notes: string | null;
}

export interface HarvestStats {
  planting_id: number;
  total_quantity: number;
  avg_quality: number | null;
  harvest_count: number;
  first_harvest: string | null;
  last_harvest: string | null;
}

export interface HarvestSummary {
  garden_id: number;
  total_harvests: number;
  first_harvest: string | null;
  last_harvest: string | null;
  by_unit: Array<{
    unit: string;
    total_quantity: number;
    avg_quality: number | null;
    harvest_count: number;
  }>;
  by_species: Array<{
    species: string;
    unit: string;
    total_quantity: number;
    harvest_count: number;
  }>;
}

export const harvestsApi = {
  log: (plantingId: number, data: HarvestCreate) =>
    api.post<ApiResponse<HarvestLog>>(`/plantings/${plantingId}/harvests`, data),

  list: (plantingId: number, skip = 0, limit = 20) =>
    api.get<ApiListResponse<HarvestLog>>(
      `/plantings/${plantingId}/harvests?skip=${skip}&limit=${limit}`,
    ),

  stats: (plantingId: number) =>
    api.get<ApiResponse<HarvestStats>>(`/plantings/${plantingId}/harvests/stats`),

  summary: (gardenId: number) =>
    api.get<ApiResponse<HarvestSummary>>(`/gardens/${gardenId}/harvests/summary`),
};

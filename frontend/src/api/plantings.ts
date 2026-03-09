import type { ApiListResponse, ApiResponse, Planting } from '../types';
import { api } from './client';

export interface PlantingCreate {
  species_id: number;
  bed_or_location?: string | null;
  quantity?: number;
  date_seeded?: string | null;
  date_transplanted?: string | null;
  status?: string;
  notes?: string | null;
  auto_generate_events?: boolean;
}

export const plantingsApi = {
  list: (gardenId: number, params?: { skip?: number; limit?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.skip) query.set('skip', String(params.skip));
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.status) query.set('status', params.status);
    return api.get<ApiListResponse<Planting>>(`/gardens/${gardenId}/plantings?${query}`);
  },

  get: (id: number) =>
    api.get<ApiResponse<Planting>>(`/plantings/${id}`),

  create: (gardenId: number, data: PlantingCreate) =>
    api.post<ApiResponse<Planting>>(`/gardens/${gardenId}/plantings`, data),

  update: (id: number, data: Partial<PlantingCreate>) =>
    api.put<ApiResponse<Planting>>(`/plantings/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/plantings/${id}`),
};

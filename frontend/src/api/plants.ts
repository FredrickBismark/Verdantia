import type { ApiListResponse, ApiResponse, PlantDetail, PlantSpecies } from '../types';
import { api } from './client';

export const plantsApi = {
  list: (params?: { skip?: number; limit?: number; search?: string; growth_habit?: string }) => {
    const query = new URLSearchParams();
    if (params?.skip) query.set('skip', String(params.skip));
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.search) query.set('search', params.search);
    if (params?.growth_habit) query.set('growth_habit', params.growth_habit);
    return api.get<ApiListResponse<PlantSpecies>>(`/plants?${query}`);
  },

  get: (id: number) =>
    api.get<ApiResponse<PlantDetail>>(`/plants/${id}`),

  create: (data: Partial<PlantSpecies>) =>
    api.post<ApiResponse<PlantSpecies>>('/plants', data),

  update: (id: number, data: Partial<PlantSpecies>) =>
    api.put<ApiResponse<PlantSpecies>>(`/plants/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/plants/${id}`),

  curate: (id: number) =>
    api.post<ApiResponse<{ status: string }>>(`/plants/${id}/curate`),
};

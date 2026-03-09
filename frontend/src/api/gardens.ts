import type { ApiListResponse, ApiResponse, Garden, GardenCreate } from '../types';
import { api } from './client';

export const gardensApi = {
  list: (skip = 0, limit = 20) =>
    api.get<ApiListResponse<Garden>>(`/gardens?skip=${skip}&limit=${limit}`),

  get: (id: number) =>
    api.get<ApiResponse<Garden>>(`/gardens/${id}`),

  create: (data: GardenCreate) =>
    api.post<ApiResponse<Garden>>('/gardens', data),

  update: (id: number, data: Partial<GardenCreate>) =>
    api.put<ApiResponse<Garden>>(`/gardens/${id}`, data),

  delete: (id: number) =>
    api.delete<void>(`/gardens/${id}`),
};

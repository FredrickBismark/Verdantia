import type { ApiListResponse, ApiResponse } from '../types';
import { api } from './client';

const BASE_URL = '/api/v1';

export interface PhotoData {
  id: number;
  planting_id: number | null;
  garden_id: number;
  file_path: string;
  thumbnail_path: string | null;
  caption: string | null;
  taken_at: string;
  tags: string[] | null;
  created_at: string;
}

export const photosApi = {
  upload: async (plantingId: number, file: File, caption?: string): Promise<ApiResponse<PhotoData>> => {
    const formData = new FormData();
    formData.append('file', file);
    if (caption) {
      formData.append('caption', caption);
    }
    const response = await fetch(`${BASE_URL}/plantings/${plantingId}/photos`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },

  list: (plantingId: number, skip = 0, limit = 20) =>
    api.get<ApiListResponse<PhotoData>>(
      `/plantings/${plantingId}/photos?skip=${skip}&limit=${limit}`,
    ),

  get: (photoId: number) =>
    api.get<ApiResponse<PhotoData>>(`/photos/${photoId}`),

  delete: async (photoId: number): Promise<void> => {
    const response = await fetch(`${BASE_URL}/photos/${photoId}`, { method: 'DELETE' });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
  },

  fileUrl: (photoId: number): string => `${BASE_URL}/photos/${photoId}/file`,

  thumbnailUrl: (photoId: number): string => `${BASE_URL}/photos/${photoId}/thumbnail`,
};

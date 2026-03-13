import type { ApiListResponse, ApiResponse } from '../types';
import { api } from './client';

export interface JournalEntry {
  id: number;
  garden_id: number;
  planting_id: number | null;
  entry_date: string;
  category: string;
  content: string;
  tags: string[] | null;
  mood: string | null;
  created_at: string;
  updated_at: string;
}

export interface JournalEntryCreate {
  planting_id?: number | null;
  entry_date: string;
  category: string;
  content: string;
  tags?: string[] | null;
  mood?: string | null;
}

export interface JournalEntryUpdate {
  planting_id?: number | null;
  entry_date?: string;
  category?: string;
  content?: string;
  tags?: string[] | null;
  mood?: string | null;
}

export const journalApi = {
  create: (gardenId: number, data: JournalEntryCreate) =>
    api.post<ApiResponse<JournalEntry>>(`/gardens/${gardenId}/journal`, data),

  list: (
    gardenId: number,
    params: {
      skip?: number;
      limit?: number;
      planting_id?: number;
      category?: string;
      start_date?: string;
      end_date?: string;
      tag?: string;
    } = {},
  ) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined) qs.set(k, String(v));
    });
    const query = qs.toString() ? `?${qs.toString()}` : '';
    return api.get<ApiListResponse<JournalEntry>>(`/gardens/${gardenId}/journal${query}`);
  },

  recent: (gardenId: number, limit = 10) =>
    api.get<ApiListResponse<JournalEntry>>(`/gardens/${gardenId}/journal/recent?limit=${limit}`),

  get: (entryId: number) =>
    api.get<ApiResponse<JournalEntry>>(`/journal/${entryId}`),

  update: (entryId: number, data: JournalEntryUpdate) =>
    api.put<ApiResponse<JournalEntry>>(`/journal/${entryId}`, data),

  delete: (entryId: number) =>
    api.delete<void>(`/journal/${entryId}`),
};

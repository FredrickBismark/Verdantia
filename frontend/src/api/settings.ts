import type { ApiResponse, AppSetting, ProviderPreset } from '../types';
import { api } from './client';

export const settingsApi = {
  list: () =>
    api.get<{ data: AppSetting[]; count: number }>('/settings'),

  update: (key: string, value: string) =>
    api.put<ApiResponse<AppSetting>>(`/settings/${key}`, { value }),

  getProviders: () =>
    api.get<{ data: Record<string, ProviderPreset> }>('/settings/llm/providers'),

  testConnection: (provider: string, model: string, apiKey?: string, baseUrl?: string) =>
    api.post<ApiResponse<{ status: string; message: string }>>('/settings/llm/test', {
      provider,
      model,
      api_key: apiKey,
      base_url: baseUrl,
    }),
};

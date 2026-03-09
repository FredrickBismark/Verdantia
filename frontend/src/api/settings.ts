import type { ApiResponse, AppSetting } from '../types';
import { api } from './client';

export const settingsApi = {
  list: () =>
    api.get<{ data: AppSetting[] }>('/settings'),

  update: (key: string, value: string) =>
    api.put<ApiResponse<AppSetting>>(`/settings/${key}`, { value }),

  getProviders: () =>
    api.get<{ data: Record<string, unknown> }>('/settings/llm/providers'),
};

import type { Alert, ApiListResponse, ApiResponse } from '../types';
import { api } from './client';

export const alertsApi = {
  list: (gardenId: number, dismissed = false, skip = 0, limit = 50) =>
    api.get<ApiListResponse<Alert>>(
      `/gardens/${gardenId}/alerts?dismissed=${dismissed}&skip=${skip}&limit=${limit}`,
    ),

  check: (gardenId: number) =>
    api.post<ApiListResponse<Alert>>(`/gardens/${gardenId}/alerts/check`),

  acknowledge: (alertId: number) =>
    api.post<ApiResponse<Alert>>(`/alerts/${alertId}/acknowledge`),

  dismiss: (alertId: number) =>
    api.post<ApiResponse<Alert>>(`/alerts/${alertId}/dismiss`),

  delete: (alertId: number) =>
    api.delete(`/alerts/${alertId}`),
};

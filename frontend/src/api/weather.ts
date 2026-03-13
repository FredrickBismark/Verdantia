import type { ApiListResponse, ApiResponse, WeatherRecord } from '../types';
import { api } from './client';

export const weatherApi = {
  current: (gardenId: number) =>
    api.get<ApiResponse<WeatherRecord>>(`/gardens/${gardenId}/weather/current`),

  forecast: (gardenId: number, days = 7) =>
    api.get<ApiListResponse<WeatherRecord>>(
      `/gardens/${gardenId}/weather/forecast?days=${days}`,
    ),

  sync: (gardenId: number) =>
    api.post<ApiResponse<{ synced: number; synced_at: string }>>(
      `/gardens/${gardenId}/weather/sync`,
    ),

  frostDates: (gardenId: number) =>
    api.get<ApiResponse<FrostDatesResult>>(`/gardens/${gardenId}/weather/frost-dates`),

  gdd: (gardenId: number, baseTempC = 10) =>
    api.get<ApiResponse<GDDResult>>(
      `/gardens/${gardenId}/weather/gdd?base_temp_c=${baseTempC}`,
    ),
};

export interface FrostDatesResult {
  garden_id: number;
  last_spring_frost: string | null;
  first_fall_frost: string | null;
  data_points: number;
  growing_season_days: number | null;
  note?: string;
}

export interface GDDResult {
  garden_id: number;
  start_date: string;
  base_temp_c: number;
  total_gdd: number;
  daily: Array<{ date: string; gdd: number; accumulated: number }>;
}

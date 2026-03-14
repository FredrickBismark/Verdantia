import type { ApiListResponse, ApiResponse, SensorReading } from '../types';
import { api } from './client';

export interface SensorInfo {
  sensor_id: string;
  garden_id: number;
  sensor_type: string;
  location: string | null;
  reading_count: number;
  first_reading: string | null;
  last_reading: string | null;
  connected: boolean;
  source: string;
}

export interface SensorStatus {
  sensor_id: string;
  garden_id: number;
  sensor_type: string;
  location: string | null;
  connected: boolean;
  health: 'active' | 'idle' | 'stale' | 'unknown';
  reading_count: number;
  last_reading: string | null;
}

export interface SensorReadingCreate {
  sensor_id: string;
  sensor_type: string;
  value: number;
  unit: string;
  timestamp?: string | null;
  location?: string | null;
}

export const sensorsApi = {
  list: (gardenId: number) =>
    api.get<ApiListResponse<SensorInfo>>(`/gardens/${gardenId}/sensors`),

  status: (gardenId: number) =>
    api.get<ApiListResponse<SensorStatus>>(`/gardens/${gardenId}/sensors/status`),

  readings: (gardenId: number, sensorId: string, limit = 100) =>
    api.get<ApiListResponse<SensorReading>>(
      `/gardens/${gardenId}/sensors/${sensorId}/readings?limit=${limit}`,
    ),

  addReading: (gardenId: number, data: SensorReadingCreate) =>
    api.post<ApiResponse<SensorReading>>(`/gardens/${gardenId}/sensors/reading`, data),
};

import type { ApiListResponse, ApiResponse, CalendarEvent } from '../types';
import { api } from './client';

export const calendarApi = {
  listEvents: (
    gardenId: number,
    params: {
      skip?: number;
      limit?: number;
      event_type?: string;
      start_date?: string;
      end_date?: string;
      completed?: boolean;
    } = {},
  ) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined) qs.set(k, String(v));
    });
    const query = qs.toString() ? `?${qs.toString()}` : '';
    return api.get<ApiListResponse<CalendarEvent>>(
      `/gardens/${gardenId}/events${query}`,
    );
  },

  createEvent: (gardenId: number, data: CalendarEventCreate) =>
    api.post<ApiResponse<CalendarEvent>>(`/gardens/${gardenId}/events`, data),

  updateEvent: (eventId: number, data: Partial<CalendarEventCreate>) =>
    api.put<ApiResponse<CalendarEvent>>(`/events/${eventId}`, data),

  deleteEvent: (eventId: number) =>
    api.delete<void>(`/events/${eventId}`),

  completeEvent: (eventId: number) =>
    api.post<ApiResponse<CalendarEvent>>(`/events/${eventId}/complete`),

  generateSchedule: (gardenId: number, plantingId: number) =>
    api.post<ApiListResponse<CalendarEvent>>(
      `/gardens/${gardenId}/events/generate?planting_id=${plantingId}`,
    ),

  weatherAlerts: (gardenId: number) =>
    api.post<ApiListResponse<CalendarEvent> & { rescheduled: CalendarEvent[]; rescheduled_count: number }>(
      `/gardens/${gardenId}/events/weather-alerts`,
    ),
};

export interface CalendarEventCreate {
  event_type: string;
  title: string;
  description?: string | null;
  scheduled_date: string;
  scheduled_time?: string | null;
  planting_id?: number | null;
  priority?: string | null;
  weather_dependent?: boolean;
  color?: string | null;
  recurrence_rule?: string | null;
}

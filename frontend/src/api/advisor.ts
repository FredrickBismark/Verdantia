import type { ApiListResponse, ApiResponse, LLMInteraction } from '../types';
import { api } from './client';

export const advisorApi = {
  chat: (gardenId: number, message: string, plantingId?: number | null) =>
    api.post<ApiResponse<ChatResponse>>(`/gardens/${gardenId}/advisor/chat`, {
      message,
      planting_id: plantingId ?? null,
    }),

  history: (gardenId: number, skip = 0, limit = 20) =>
    api.get<ApiListResponse<LLMInteraction>>(
      `/gardens/${gardenId}/advisor/history?skip=${skip}&limit=${limit}`,
    ),

  submitFeedback: (interactionId: number, feedback: string) =>
    api.post<ApiResponse<{ status: string }>>(
      `/advisor/interactions/${interactionId}/feedback`,
      { feedback },
    ),
};

export interface ChatResponse {
  response: string;
  model_used: string;
  provider: string;
  context_summary: string;
  interaction_id: number;
}

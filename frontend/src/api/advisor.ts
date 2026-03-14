import type { ApiListResponse, ApiResponse, LLMInteraction } from '../types';
import { api } from './client';

export interface ChatResponse {
  response: string;
  model_used: string;
  provider: string;
  context_summary: string;
  interaction_id: number;
}

export interface StreamChunk {
  chunk: string;
  done: boolean;
  interaction_id?: number | null;
}

export interface DiagnosisResponse {
  diagnosis: string;
  interaction_id: number;
  model_used: string;
  provider: string;
}

export const advisorApi = {
  diagnose: (plantingId: number, photoId: number, question?: string | null) =>
    api.post<ApiResponse<DiagnosisResponse>>(`/plantings/${plantingId}/advisor/diagnose`, {
      photo_id: photoId,
      question: question ?? null,
    }),

  chat: (gardenId: number, message: string, plantingId?: number | null) =>
    api.post<ApiResponse<ChatResponse>>(`/gardens/${gardenId}/advisor/chat`, {
      message,
      planting_id: plantingId ?? null,
    }),

  chatStream: async function* (
    gardenId: number,
    message: string,
    plantingId?: number | null,
    signal?: AbortSignal,
  ): AsyncGenerator<StreamChunk> {
    const response = await fetch(`/api/v1/gardens/${gardenId}/advisor/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, planting_id: plantingId ?? null }),
      signal,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const json = trimmed.slice(6);
          if (!json) continue;
          try {
            yield JSON.parse(json) as StreamChunk;
          } catch {
            // skip malformed chunks
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

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

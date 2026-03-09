import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { gardensApi } from '../api/gardens';
import type { GardenCreate } from '../types';

export const useGardens = (skip = 0, limit = 20) => {
  return useQuery({
    queryKey: ['gardens', skip, limit],
    queryFn: () => gardensApi.list(skip, limit),
  });
};

export const useGarden = (id: number | null) => {
  return useQuery({
    queryKey: ['gardens', id],
    queryFn: () => gardensApi.get(id!),
    enabled: id !== null,
  });
};

export const useCreateGarden = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GardenCreate) => gardensApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['gardens'] });
    },
  });
};

export const useUpdateGarden = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<GardenCreate> }) =>
      gardensApi.update(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['gardens'] });
    },
  });
};

export const useDeleteGarden = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => gardensApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['gardens'] });
    },
  });
};

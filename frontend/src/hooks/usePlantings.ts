import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { plantingsApi } from '../api/plantings';
import type { PlantingCreate } from '../api/plantings';

export const usePlantings = (gardenId: number | null, params?: { skip?: number; limit?: number; status?: string }) => {
  return useQuery({
    queryKey: ['plantings', gardenId, params],
    queryFn: () => plantingsApi.list(gardenId!, params),
    enabled: gardenId !== null,
  });
};

export const usePlanting = (id: number | null) => {
  return useQuery({
    queryKey: ['plantings', 'detail', id],
    queryFn: () => plantingsApi.get(id!),
    enabled: id !== null,
  });
};

export const useCreatePlanting = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ gardenId, data }: { gardenId: number; data: PlantingCreate }) =>
      plantingsApi.create(gardenId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plantings'] });
    },
  });
};

export const useUpdatePlanting = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<PlantingCreate> }) =>
      plantingsApi.update(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plantings'] });
    },
  });
};

export const useDeletePlanting = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => plantingsApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plantings'] });
    },
  });
};

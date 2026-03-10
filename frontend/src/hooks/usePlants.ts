import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { plantsApi } from '../api/plants';
import type { PlantSpecies } from '../types';

export const usePlants = (params?: { skip?: number; limit?: number; search?: string; growth_habit?: string }) => {
  return useQuery({
    queryKey: ['plants', params],
    queryFn: () => plantsApi.list(params),
  });
};

export const usePlant = (id: number | null) => {
  return useQuery({
    queryKey: ['plants', id],
    queryFn: () => plantsApi.get(id!),
    enabled: id !== null,
  });
};

export const useCreatePlant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<PlantSpecies>) => plantsApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plants'] });
    },
  });
};

export const useUpdatePlant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<PlantSpecies> }) =>
      plantsApi.update(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plants'] });
    },
  });
};

export const useDeletePlant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => plantsApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plants'] });
    },
  });
};

export const useCuratePlant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => plantsApi.curate(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plants'] });
    },
  });
};

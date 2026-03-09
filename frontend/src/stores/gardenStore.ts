import { create } from 'zustand';

interface GardenStore {
  selectedGardenId: number | null;
  setSelectedGardenId: (id: number | null) => void;
}

export const useGardenStore = create<GardenStore>((set) => ({
  selectedGardenId: null,
  setSelectedGardenId: (id) => set({ selectedGardenId: id }),
}));

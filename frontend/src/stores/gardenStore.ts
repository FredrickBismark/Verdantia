import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface GardenStore {
  selectedGardenId: number | null;
  setSelectedGardenId: (id: number | null) => void;
}

export const useGardenStore = create<GardenStore>()(
  persist(
    (set) => ({
      selectedGardenId: null,
      setSelectedGardenId: (id) => set({ selectedGardenId: id }),
    }),
    { name: 'verdanta-selected-garden' },
  ),
);

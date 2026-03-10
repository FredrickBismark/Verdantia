import { useState } from 'react';
import { Plus, Pencil, Trash2, MapPin, Leaf } from 'lucide-react';
import { useGardens, useCreateGarden, useUpdateGarden, useDeleteGarden } from '../hooks/useGardens';
import { usePlantings, useCreatePlanting, useUpdatePlanting, useDeletePlanting } from '../hooks/usePlantings';
import { usePlants } from '../hooks/usePlants';
import { useGardenStore } from '../stores/gardenStore';
import type { Garden, GardenCreate, Planting } from '../types';
import type { PlantingCreate } from '../api/plantings';

const EMPTY_FORM: GardenCreate = {
  name: '',
  latitude: 0,
  longitude: 0,
  timezone: 'UTC',
};

export const GardensPage = (): React.ReactElement => {
  const { data, isLoading, isError } = useGardens();
  const createGarden = useCreateGarden();
  const updateGarden = useUpdateGarden();
  const deleteGarden = useDeleteGarden();
  const { selectedGardenId, setSelectedGardenId } = useGardenStore();

  const [showForm, setShowForm] = useState(false);
  const [editingGarden, setEditingGarden] = useState<Garden | null>(null);
  const [form, setForm] = useState<GardenCreate>(EMPTY_FORM);

  const gardens = data?.data ?? [];

  const openCreate = (): void => {
    setEditingGarden(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  };

  const openEdit = (garden: Garden): void => {
    setEditingGarden(garden);
    setForm({
      name: garden.name,
      latitude: garden.latitude,
      longitude: garden.longitude,
      elevation_m: garden.elevation_m,
      usda_zone: garden.usda_zone,
      soil_type_default: garden.soil_type_default,
      timezone: garden.timezone,
      notes: garden.notes,
    });
    setShowForm(true);
  };

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (editingGarden) {
      updateGarden.mutate({ id: editingGarden.id, data: form }, {
        onSuccess: () => setShowForm(false),
      });
    } else {
      createGarden.mutate(form, {
        onSuccess: () => setShowForm(false),
      });
    }
  };

  const handleDelete = (id: number): void => {
    if (!window.confirm('Are you sure you want to delete this garden? All plantings in it will also be removed.')) return;
    if (selectedGardenId === id) setSelectedGardenId(null);
    deleteGarden.mutate(id);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Gardens</h1>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Garden
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            {editingGarden ? 'Edit Garden' : 'New Garden'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
                <input
                  type="text"
                  value={form.timezone ?? 'UTC'}
                  onChange={(e) => setForm({ ...form, timezone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Latitude *</label>
                <input
                  type="number"
                  step="any"
                  required
                  value={form.latitude}
                  onChange={(e) => setForm({ ...form, latitude: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Longitude *</label>
                <input
                  type="number"
                  step="any"
                  required
                  value={form.longitude}
                  onChange={(e) => setForm({ ...form, longitude: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">USDA Zone</label>
                <input
                  type="text"
                  value={form.usda_zone ?? ''}
                  onChange={(e) => setForm({ ...form, usda_zone: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Elevation (m)</label>
                <input
                  type="number"
                  step="any"
                  value={form.elevation_m ?? ''}
                  onChange={(e) => setForm({ ...form, elevation_m: e.target.value ? parseFloat(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Default Soil Type</label>
                <input
                  type="text"
                  value={form.soil_type_default ?? ''}
                  onChange={(e) => setForm({ ...form, soil_type_default: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                rows={3}
                value={form.notes ?? ''}
                onChange={(e) => setForm({ ...form, notes: e.target.value || null })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={createGarden.isPending || updateGarden.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {editingGarden ? 'Update' : 'Create'} Garden
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {isError ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Failed to load gardens. Please check your connection and try again.
        </div>
      ) : isLoading ? (
        <div className="text-gray-500 text-sm">Loading gardens...</div>
      ) : gardens.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No gardens yet</h3>
          <p className="text-gray-500 text-sm mb-4">Create your first garden to get started.</p>
          <button
            onClick={openCreate}
            className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
          >
            Add Garden
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {gardens.map((garden) => (
            <div
              key={garden.id}
              onClick={() => setSelectedGardenId(garden.id)}
              className={`bg-white rounded-lg border p-5 cursor-pointer transition-colors ${
                selectedGardenId === garden.id
                  ? 'border-green-500 ring-2 ring-green-100'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-base font-semibold text-gray-900">{garden.name}</h3>
                <div className="flex gap-1">
                  <button
                    onClick={(e) => { e.stopPropagation(); openEdit(garden); }}
                    className="p-1.5 text-gray-400 hover:text-gray-600 rounded"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(garden.id); }}
                    className="p-1.5 text-gray-400 hover:text-red-600 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="space-y-1 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>{garden.latitude.toFixed(4)}, {garden.longitude.toFixed(4)}</span>
                </div>
                {garden.usda_zone && <div>Zone {garden.usda_zone}</div>}
                {garden.soil_type_default && <div>Soil: {garden.soil_type_default}</div>}
                <div className="text-xs text-gray-400">{garden.timezone}</div>
              </div>
              {garden.notes && (
                <p className="mt-3 text-sm text-gray-600 line-clamp-2">{garden.notes}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedGardenId && (
        <PlantingsPanel gardenId={selectedGardenId} />
      )}
    </div>
  );
};

const PLANTING_STATUSES = ['planned', 'planted', 'active', 'harvesting', 'completed', 'removed'];

const EMPTY_PLANTING: PlantingCreate = {
  species_id: 0,
  bed_or_location: '',
  quantity: 1,
  date_seeded: '',
  status: 'planned',
  notes: '',
};

const PlantingsPanel = ({ gardenId }: { gardenId: number }): React.ReactElement => {
  const { data: plantingsData, isLoading, isError } = usePlantings(gardenId);
  const { data: plantsData } = usePlants();
  const createPlanting = useCreatePlanting();
  const updatePlanting = useUpdatePlanting();
  const deletePlanting = useDeletePlanting();

  const [showForm, setShowForm] = useState(false);
  const [editingPlanting, setEditingPlanting] = useState<Planting | null>(null);
  const [form, setForm] = useState<PlantingCreate>(EMPTY_PLANTING);

  const plantings = plantingsData?.data ?? [];
  const plants = plantsData?.data ?? [];

  const openCreate = (): void => {
    setEditingPlanting(null);
    setForm(EMPTY_PLANTING);
    setShowForm(true);
  };

  const openEdit = (planting: Planting): void => {
    setEditingPlanting(planting);
    setForm({
      species_id: planting.species_id,
      bed_or_location: planting.bed_or_location ?? '',
      quantity: planting.quantity,
      date_seeded: planting.date_seeded ?? '',
      status: planting.status,
      notes: planting.notes ?? '',
    });
    setShowForm(true);
  };

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    const payload: PlantingCreate = {
      ...form,
      bed_or_location: form.bed_or_location || null,
      date_seeded: form.date_seeded || null,
      notes: form.notes || null,
    };

    if (editingPlanting) {
      updatePlanting.mutate({ id: editingPlanting.id, data: payload }, {
        onSuccess: () => setShowForm(false),
      });
    } else {
      createPlanting.mutate({ gardenId, data: payload }, {
        onSuccess: () => setShowForm(false),
      });
    }
  };

  const getPlantName = (speciesId: number): string => {
    const plant = plants.find((p) => p.id === speciesId);
    return plant?.common_name ?? `Species #${speciesId}`;
  };

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Leaf className="w-5 h-5 text-green-600" />
          Plantings
        </h2>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Planting
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-4">
          <h3 className="text-base font-medium text-gray-900 mb-4">
            {editingPlanting ? 'Edit Planting' : 'New Planting'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Plant Species *</label>
                <select
                  required
                  value={form.species_id}
                  onChange={(e) => setForm({ ...form, species_id: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value={0} disabled>Select a plant...</option>
                  {plants.map((p) => (
                    <option key={p.id} value={p.id}>{p.common_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location / Bed</label>
                <input
                  type="text"
                  value={form.bed_or_location ?? ''}
                  onChange={(e) => setForm({ ...form, bed_or_location: e.target.value })}
                  placeholder="e.g. Raised bed A"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                <input
                  type="number"
                  min={1}
                  value={form.quantity ?? 1}
                  onChange={(e) => setForm({ ...form, quantity: parseInt(e.target.value) || 1 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date Seeded</label>
                <input
                  type="date"
                  value={form.date_seeded ?? ''}
                  onChange={(e) => setForm({ ...form, date_seeded: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={form.status ?? 'planned'}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  {PLANTING_STATUSES.map((s) => (
                    <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                rows={2}
                value={form.notes ?? ''}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={createPlanting.isPending || updatePlanting.isPending || form.species_id === 0}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {editingPlanting ? 'Update' : 'Create'} Planting
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {isError ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Failed to load plantings. Please try again.
        </div>
      ) : isLoading ? (
        <div className="text-gray-500 text-sm">Loading plantings...</div>
      ) : plantings.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Leaf className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">No plantings in this garden yet.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Plant</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Location</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Qty</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase hidden md:table-cell">Seeded</th>
                <th className="w-20"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {plantings.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-sm font-medium text-gray-900">{getPlantName(p.species_id)}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{p.bed_or_location ?? '-'}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{p.quantity}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      statusColor(p.status)
                    }`}>
                      {p.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-600 hidden md:table-cell">{p.date_seeded ?? '-'}</td>
                  <td className="px-4 py-2">
                    <div className="flex gap-1">
                      <button
                        onClick={() => openEdit(p)}
                        className="p-1.5 text-gray-400 hover:text-gray-600 rounded"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          if (window.confirm('Are you sure you want to delete this planting?')) {
                            deletePlanting.mutate(p.id);
                          }
                        }}
                        className="p-1.5 text-gray-400 hover:text-red-600 rounded"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const statusColor = (status: string): string => {
  const colors: Record<string, string> = {
    planned: 'bg-blue-100 text-blue-700',
    planted: 'bg-green-100 text-green-700',
    active: 'bg-green-100 text-green-700',
    harvesting: 'bg-amber-100 text-amber-700',
    completed: 'bg-gray-100 text-gray-600',
    removed: 'bg-red-100 text-red-600',
  };
  return colors[status] ?? 'bg-gray-100 text-gray-600';
};

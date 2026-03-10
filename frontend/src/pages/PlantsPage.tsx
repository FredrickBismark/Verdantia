import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Search, ArrowLeft, Pencil, Trash2, Sprout, Sparkles, Loader2 } from 'lucide-react';
import { usePlants, usePlant, useCreatePlant, useUpdatePlant, useDeletePlant, useCuratePlant } from '../hooks/usePlants';
import type { PlantSpecies } from '../types';

interface PlantFormData {
  common_name: string;
  scientific_name: string;
  family: string;
  variety: string;
  growth_habit: string;
  days_to_maturity_min: number | null;
  days_to_maturity_max: number | null;
  sun_requirement: string;
  water_requirement: string;
  frost_tolerance: string;
  spacing_cm: number | null;
  depth_cm: number | null;
}

const EMPTY_FORM: PlantFormData = {
  common_name: '',
  scientific_name: '',
  family: '',
  variety: '',
  growth_habit: '',
  days_to_maturity_min: null,
  days_to_maturity_max: null,
  sun_requirement: '',
  water_requirement: '',
  frost_tolerance: '',
  spacing_cm: null,
  depth_cm: null,
};

const SUN_OPTIONS = ['Full Sun', 'Partial Sun', 'Partial Shade', 'Full Shade'];
const WATER_OPTIONS = ['Low', 'Moderate', 'High'];
const FROST_OPTIONS = ['Hardy', 'Semi-Hardy', 'Tender'];
const GROWTH_HABITS = ['Annual', 'Biennial', 'Perennial', 'Vine', 'Shrub', 'Tree'];

const CONFIDENCE_COLORS: Record<string, string> = {
  high: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-orange-100 text-orange-700',
  contradicted: 'bg-red-100 text-red-700',
};

const PlantDetail = ({ plantId, onBack }: { plantId: number; onBack: () => void }): React.ReactElement => {
  const { data, isLoading } = usePlant(plantId);
  const curatePlant = useCuratePlant();
  const plant = data?.data;

  if (isLoading) return <div className="text-gray-500 text-sm">Loading...</div>;
  if (!plant) return <div className="text-gray-500 text-sm">Plant not found</div>;

  return (
    <div>
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft className="w-4 h-4" /> Back to plants
      </button>
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{plant.common_name}</h2>
            {plant.scientific_name && (
              <p className="text-sm text-gray-500 italic">{plant.scientific_name}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
              plant.curation_status === 'curated' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
            }`}>
              {plant.curation_status}
            </span>
            <button
              onClick={() => curatePlant.mutate(plantId)}
              disabled={curatePlant.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700 transition-colors disabled:opacity-50"
            >
              {curatePlant.isPending ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Curating...</>
              ) : (
                <><Sparkles className="w-3.5 h-3.5" /> {plant.curation_status === 'curated' ? 'Re-curate' : 'Curate'}</>
              )}
            </button>
          </div>
        </div>

        {curatePlant.isError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            Curation failed: {curatePlant.error.message}
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          {plant.family && <Field label="Family" value={plant.family} />}
          {plant.variety && <Field label="Variety" value={plant.variety} />}
          {plant.growth_habit && <Field label="Growth Habit" value={plant.growth_habit} />}
          {plant.sun_requirement && <Field label="Sun" value={plant.sun_requirement} />}
          {plant.water_requirement && <Field label="Water" value={plant.water_requirement} />}
          {plant.frost_tolerance && <Field label="Frost Tolerance" value={plant.frost_tolerance} />}
          {(plant.days_to_maturity_min || plant.days_to_maturity_max) && (
            <Field label="Days to Maturity" value={
              plant.days_to_maturity_min && plant.days_to_maturity_max
                ? `${plant.days_to_maturity_min}-${plant.days_to_maturity_max}`
                : String(plant.days_to_maturity_min ?? plant.days_to_maturity_max)
            } />
          )}
          {plant.spacing_cm && <Field label="Spacing" value={`${plant.spacing_cm} cm`} />}
          {plant.depth_cm && <Field label="Planting Depth" value={`${plant.depth_cm} cm`} />}
          {plant.curation_model && <Field label="Curated By" value={plant.curation_model} />}
        </div>

        {plant.dossier_sections.length > 0 && (
          <div className="mt-6 space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Dossier</h3>
            {plant.dossier_sections
              .sort((a, b) => a.display_order - b.display_order)
              .map((section) => (
              <div key={section.id} className="border-l-2 border-green-300 pl-4">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-sm font-medium text-gray-900">{section.title}</h4>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    CONFIDENCE_COLORS[section.confidence] ?? 'bg-gray-100 text-gray-600'
                  }`}>
                    {section.confidence}
                  </span>
                </div>
                <p className="text-sm text-gray-600 whitespace-pre-line">{section.content}</p>
              </div>
            ))}
          </div>
        )}

        {plant.data_sources.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">Data Sources</h3>
            <div className="space-y-2">
              {plant.data_sources.map((source) => (
                <div key={source.id} className="flex items-center justify-between text-sm bg-gray-50 rounded px-3 py-2">
                  <div>
                    <span className="font-medium text-gray-900">{source.source_name}</span>
                    <span className="text-gray-400 ml-2 text-xs">{source.source_type}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    {source.confidence_score !== null && (
                      <span className="text-xs text-gray-500">
                        {Math.round(source.confidence_score * 100)}% confidence
                      </span>
                    )}
                    {source.source_url && (
                      <a href={source.source_url} target="_blank" rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline">
                        View source
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const Field = ({ label, value }: { label: string; value: string }): React.ReactElement => (
  <div>
    <dt className="text-gray-500 text-xs uppercase tracking-wide">{label}</dt>
    <dd className="text-gray-900 mt-0.5">{value}</dd>
  </div>
);

export const PlantsPage = (): React.ReactElement => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingPlant, setEditingPlant] = useState<PlantSpecies | null>(null);
  const [form, setForm] = useState<PlantFormData>(EMPTY_FORM);

  const { data, isLoading, isError } = usePlants({ search: search || undefined });
  const createPlant = useCreatePlant();
  const updatePlant = useUpdatePlant();
  const deletePlant = useDeletePlant();

  const plants = data?.data ?? [];
  const detailId = id ? parseInt(id) : null;

  if (detailId) {
    return <PlantDetail plantId={detailId} onBack={() => navigate('/plants')} />;
  }

  const openCreate = (): void => {
    setEditingPlant(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  };

  const openEdit = (plant: PlantSpecies): void => {
    setEditingPlant(plant);
    setForm({
      common_name: plant.common_name,
      scientific_name: plant.scientific_name ?? '',
      family: plant.family ?? '',
      variety: plant.variety ?? '',
      growth_habit: plant.growth_habit ?? '',
      days_to_maturity_min: plant.days_to_maturity_min,
      days_to_maturity_max: plant.days_to_maturity_max,
      sun_requirement: plant.sun_requirement ?? '',
      water_requirement: plant.water_requirement ?? '',
      frost_tolerance: plant.frost_tolerance ?? '',
      spacing_cm: plant.spacing_cm,
      depth_cm: plant.depth_cm,
    });
    setShowForm(true);
  };

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    const payload: Partial<PlantSpecies> = {
      common_name: form.common_name,
      scientific_name: form.scientific_name || null,
      family: form.family || null,
      variety: form.variety || null,
      growth_habit: form.growth_habit || null,
      days_to_maturity_min: form.days_to_maturity_min,
      days_to_maturity_max: form.days_to_maturity_max,
      sun_requirement: form.sun_requirement || null,
      water_requirement: form.water_requirement || null,
      frost_tolerance: form.frost_tolerance || null,
      spacing_cm: form.spacing_cm,
      depth_cm: form.depth_cm,
    };

    if (editingPlant) {
      updatePlant.mutate({ id: editingPlant.id, data: payload }, {
        onSuccess: () => setShowForm(false),
      });
    } else {
      createPlant.mutate(payload, {
        onSuccess: () => setShowForm(false),
      });
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Plants</h1>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Plant
        </button>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search plants..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>

      {showForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            {editingPlant ? 'Edit Plant' : 'New Plant'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Common Name *</label>
                <input
                  type="text"
                  required
                  value={form.common_name}
                  onChange={(e) => setForm({ ...form, common_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Scientific Name</label>
                <input
                  type="text"
                  value={form.scientific_name}
                  onChange={(e) => setForm({ ...form, scientific_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Family</label>
                <input
                  type="text"
                  value={form.family}
                  onChange={(e) => setForm({ ...form, family: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Variety</label>
                <input
                  type="text"
                  value={form.variety}
                  onChange={(e) => setForm({ ...form, variety: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Growth Habit</label>
                <select
                  value={form.growth_habit}
                  onChange={(e) => setForm({ ...form, growth_habit: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  {GROWTH_HABITS.map((h) => <option key={h} value={h}>{h}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sun Requirement</label>
                <select
                  value={form.sun_requirement}
                  onChange={(e) => setForm({ ...form, sun_requirement: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  {SUN_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Water Requirement</label>
                <select
                  value={form.water_requirement}
                  onChange={(e) => setForm({ ...form, water_requirement: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  {WATER_OPTIONS.map((w) => <option key={w} value={w}>{w}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Frost Tolerance</label>
                <select
                  value={form.frost_tolerance}
                  onChange={(e) => setForm({ ...form, frost_tolerance: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  {FROST_OPTIONS.map((f) => <option key={f} value={f}>{f}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Days to Maturity (min)</label>
                <input
                  type="number"
                  value={form.days_to_maturity_min ?? ''}
                  onChange={(e) => setForm({ ...form, days_to_maturity_min: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Days to Maturity (max)</label>
                <input
                  type="number"
                  value={form.days_to_maturity_max ?? ''}
                  onChange={(e) => setForm({ ...form, days_to_maturity_max: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Spacing (cm)</label>
                <input
                  type="number"
                  value={form.spacing_cm ?? ''}
                  onChange={(e) => setForm({ ...form, spacing_cm: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Planting Depth (cm)</label>
                <input
                  type="number"
                  value={form.depth_cm ?? ''}
                  onChange={(e) => setForm({ ...form, depth_cm: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={createPlant.isPending || updatePlant.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {editingPlant ? 'Update' : 'Create'} Plant
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
          Failed to load plants. Please check your connection and try again.
        </div>
      ) : isLoading ? (
        <div className="text-gray-500 text-sm">Loading plants...</div>
      ) : plants.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Sprout className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {search ? 'No plants found' : 'No plants yet'}
          </h3>
          <p className="text-gray-500 text-sm mb-4">
            {search ? 'Try a different search term.' : 'Add your first plant species to get started.'}
          </p>
          {!search && (
            <button
              onClick={openCreate}
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
            >
              Add Plant
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Name</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide hidden md:table-cell">Family</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide hidden lg:table-cell">Growth</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide hidden lg:table-cell">Sun</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                <th className="w-20"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {plants.map((plant) => (
                <tr
                  key={plant.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/plants/${plant.id}`)}
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900 text-sm">{plant.common_name}</div>
                    {plant.scientific_name && (
                      <div className="text-xs text-gray-500 italic">{plant.scientific_name}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden md:table-cell">{plant.family ?? '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden lg:table-cell">{plant.growth_habit ?? '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden lg:table-cell">{plant.sun_requirement ?? '-'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      plant.curation_status === 'curated' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {plant.curation_status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); openEdit(plant); }}
                        className="p-1.5 text-gray-400 hover:text-gray-600 rounded"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm('Are you sure you want to delete this plant? All associated plantings will also be removed.')) {
                            deletePlant.mutate(plant.id);
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
          {data && data.count > plants.length && (
            <div className="px-4 py-3 border-t border-gray-100 text-sm text-gray-500">
              Showing {plants.length} of {data.count} plants
            </div>
          )}
        </div>
      )}
    </div>
  );
};

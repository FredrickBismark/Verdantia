import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { Plus, Search, ArrowLeft, Pencil, Trash2, Sprout, Sparkles, Loader2, Camera, BookOpen, Database, Apple, FlaskConical, StickyNote } from 'lucide-react';
import { usePlants, usePlant, useCreatePlant, useUpdatePlant, useDeletePlant, useCuratePlant } from '../hooks/usePlants';
import { usePlantings } from '../hooks/usePlantings';
import { useGardenStore } from '../stores/gardenStore';
import { PhotoUpload } from '../components/PhotoUpload';
import { PhotoGallery } from '../components/PhotoGallery';
import { HarvestLogger } from '../components/HarvestLogger';
import { HarvestChart } from '../components/HarvestChart';
import { soilApi } from '../api/soil';
import { journalApi } from '../api/journal';
import type { PlantSpecies, SoilTest } from '../types';

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

type DetailTab = 'overview' | 'photos' | 'harvest' | 'soil' | 'notes' | 'sources';

const PlantDetail = ({ plantId, onBack }: { plantId: number; onBack: () => void }): React.ReactElement => {
  const { data, isLoading } = usePlant(plantId);
  const curatePlant = useCuratePlant();
  const plant = data?.data;
  const [activeTab, setActiveTab] = useState<DetailTab>('overview');
  const { selectedGardenId } = useGardenStore();
  const { data: plantingsData } = usePlantings(selectedGardenId, { limit: 100 });
  const speciesPlantings = (plantingsData?.data ?? []).filter((p) => p.species_id === plantId);

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

        <div className="flex gap-1 border-b border-gray-200 mt-4 mb-4">
          {([
            { key: 'overview' as DetailTab, label: 'Overview', icon: BookOpen },
            { key: 'photos' as DetailTab, label: 'Photos', icon: Camera },
            { key: 'harvest' as DetailTab, label: 'Harvest', icon: Apple },
            { key: 'soil' as DetailTab, label: 'Soil', icon: FlaskConical },
            { key: 'notes' as DetailTab, label: 'Notes', icon: StickyNote },
            { key: 'sources' as DetailTab, label: 'Sources', icon: Database },
          ]).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                activeTab === key
                  ? 'border-green-600 text-green-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <>
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
          </>
        )}

        {activeTab === 'photos' && (
          <div className="space-y-6">
            {speciesPlantings.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-6">
                No plantings found for this species. Create a planting to add photos.
              </p>
            ) : (
              speciesPlantings.map((planting) => (
                <div key={planting.id} className="space-y-3">
                  <h4 className="text-sm font-medium text-gray-700">
                    {planting.bed_or_location ?? `Planting #${planting.id}`}
                    <span className="text-gray-400 ml-2 text-xs">({planting.status})</span>
                  </h4>
                  <PhotoUpload plantingId={planting.id} />
                  <PhotoGallery plantingId={planting.id} />
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'harvest' && (
          <div className="space-y-6">
            {speciesPlantings.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-6">
                No plantings found for this species. Create a planting to log harvests.
              </p>
            ) : (
              speciesPlantings.map((planting) => (
                <div key={planting.id} className="space-y-3">
                  <h4 className="text-sm font-medium text-gray-700">
                    {planting.bed_or_location ?? `Planting #${planting.id}`}
                    <span className="text-gray-400 ml-2 text-xs">({planting.status})</span>
                  </h4>
                  <HarvestLogger plantingId={planting.id} />
                  <HarvestChart plantingId={planting.id} />
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'soil' && selectedGardenId && (
          <SoilTabContent gardenId={selectedGardenId} />
        )}

        {activeTab === 'notes' && selectedGardenId && (
          <NotesTabContent
            gardenId={selectedGardenId}
            plantingIds={speciesPlantings.map((p) => p.id)}
            speciesName={plant.common_name}
          />
        )}

        {activeTab === 'sources' && (
          <div>
            {plant.data_sources.length > 0 ? (
              <div className="space-y-3">
                {plant.data_sources.map((source) => (
                  <SourceCard key={source.id} source={source} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-6">
                No data sources yet. Curate this plant to fetch external data.
              </p>
            )}
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

const TEXTURES = ['Sandy', 'Loamy', 'Clay', 'Silty', 'Chalky', 'Peaty'];

const SoilTabContent = ({ gardenId }: { gardenId: number }): React.ReactElement => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    test_date: new Date().toISOString().split('T')[0],
    location: '',
    ph: '',
    nitrogen_ppm: '',
    phosphorus_ppm: '',
    potassium_ppm: '',
    organic_matter_pct: '',
    texture: '',
    notes: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['soil-tests', gardenId],
    queryFn: () => soilApi.list(gardenId),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      soilApi.create(gardenId, {
        test_date: form.test_date,
        location: form.location || null,
        ph: form.ph ? parseFloat(form.ph) : null,
        nitrogen_ppm: form.nitrogen_ppm ? parseFloat(form.nitrogen_ppm) : null,
        phosphorus_ppm: form.phosphorus_ppm ? parseFloat(form.phosphorus_ppm) : null,
        potassium_ppm: form.potassium_ppm ? parseFloat(form.potassium_ppm) : null,
        organic_matter_pct: form.organic_matter_pct ? parseFloat(form.organic_matter_pct) : null,
        texture: form.texture || null,
        notes: form.notes || null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['soil-tests', gardenId] });
      setShowForm(false);
      setForm({
        test_date: new Date().toISOString().split('T')[0],
        location: '', ph: '', nitrogen_ppm: '', phosphorus_ppm: '',
        potassium_ppm: '', organic_matter_pct: '', texture: '', notes: '',
      });
    },
  });

  const tests: SoilTest[] = data?.data ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">{tests.length} soil test{tests.length !== 1 ? 's' : ''} recorded</span>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 text-xs px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          <Plus size={12} /> Add Test
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }}
          className="bg-gray-50 rounded-lg p-4 space-y-3"
        >
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Test Date</label>
              <input type="date" value={form.test_date} onChange={(e) => setForm({ ...form, test_date: e.target.value })}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Location</label>
              <input type="text" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })}
                placeholder="e.g. Bed A" className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">pH</label>
              <input type="number" step="0.1" min="0" max="14" value={form.ph} onChange={(e) => setForm({ ...form, ph: e.target.value })}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nitrogen (ppm)</label>
              <input type="number" step="0.1" value={form.nitrogen_ppm} onChange={(e) => setForm({ ...form, nitrogen_ppm: e.target.value })}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Phosphorus (ppm)</label>
              <input type="number" step="0.1" value={form.phosphorus_ppm} onChange={(e) => setForm({ ...form, phosphorus_ppm: e.target.value })}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Potassium (ppm)</label>
              <input type="number" step="0.1" value={form.potassium_ppm} onChange={(e) => setForm({ ...form, potassium_ppm: e.target.value })}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Organic Matter (%)</label>
              <input type="number" step="0.1" value={form.organic_matter_pct} onChange={(e) => setForm({ ...form, organic_matter_pct: e.target.value })}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Texture</label>
              <select value={form.texture} onChange={(e) => setForm({ ...form, texture: e.target.value })}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm">
                <option value="">Select...</option>
                {TEXTURES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={2} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={createMutation.isPending}
              className="px-3 py-1.5 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700 disabled:opacity-50">
              {createMutation.isPending ? 'Saving...' : 'Save Test'}
            </button>
            <button type="button" onClick={() => setShowForm(false)}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded text-xs font-medium hover:bg-gray-300">
              Cancel
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="text-sm text-gray-400">Loading soil tests...</div>
      ) : tests.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-6">No soil tests recorded yet.</p>
      ) : (
        <div className="space-y-2">
          {tests.map((test) => (
            <SoilTestCard key={test.id} test={test} />
          ))}
        </div>
      )}
    </div>
  );
};

const SoilTestCard = ({ test }: { test: SoilTest }): React.ReactElement => {
  const phColor = test.ph !== null
    ? test.ph < 5.5 ? 'text-red-600' : test.ph > 7.5 ? 'text-blue-600' : 'text-green-600'
    : '';

  return (
    <div className="bg-gray-50 rounded-lg p-3 text-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-gray-900">
          {new Date(test.test_date).toLocaleDateString()}
          {test.location && <span className="text-gray-500 ml-2">— {test.location}</span>}
        </span>
        {test.texture && <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">{test.texture}</span>}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
        {test.ph !== null && (
          <div><span className="text-gray-500">pH</span> <span className={`font-medium ${phColor}`}>{test.ph}</span></div>
        )}
        {test.nitrogen_ppm !== null && (
          <div><span className="text-gray-500">N</span> <span className="font-medium">{test.nitrogen_ppm} ppm</span></div>
        )}
        {test.phosphorus_ppm !== null && (
          <div><span className="text-gray-500">P</span> <span className="font-medium">{test.phosphorus_ppm} ppm</span></div>
        )}
        {test.potassium_ppm !== null && (
          <div><span className="text-gray-500">K</span> <span className="font-medium">{test.potassium_ppm} ppm</span></div>
        )}
        {test.organic_matter_pct !== null && (
          <div><span className="text-gray-500">OM</span> <span className="font-medium">{test.organic_matter_pct}%</span></div>
        )}
      </div>
      {test.notes && <p className="text-xs text-gray-500 mt-2">{test.notes}</p>}
    </div>
  );
};

interface NotesTabProps {
  gardenId: number;
  plantingIds: number[];
  speciesName: string;
}

const NotesTabContent = ({ gardenId, plantingIds, speciesName }: NotesTabProps): React.ReactElement => {
  const { data, isLoading } = useQuery({
    queryKey: ['journal', 'species-notes', gardenId, plantingIds],
    queryFn: () => journalApi.list(gardenId, { limit: 50 }),
    enabled: gardenId > 0,
  });

  // Filter journal entries that are related to this species' plantings
  const entries = (data?.data ?? []).filter(
    (e) => e.planting_id !== null && plantingIds.includes(e.planting_id)
  );

  if (isLoading) return <div className="text-sm text-gray-400">Loading notes...</div>;

  if (entries.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <StickyNote size={32} className="mx-auto mb-2 text-gray-300" />
        <p className="text-sm">No journal entries linked to {speciesName} plantings.</p>
        <p className="text-xs mt-1">Create observations from the Journal page to see them here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div key={entry.id} className="border-l-2 border-green-300 pl-4 py-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-gray-900">
              {new Date(entry.entry_date).toLocaleDateString()}
            </span>
            <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded capitalize">
              {entry.category.replace('_', ' ')}
            </span>
            {entry.mood && (
              <span className="text-xs text-gray-400">{entry.mood}</span>
            )}
          </div>
          <div className="prose prose-sm max-w-none text-gray-700">
            <ReactMarkdown>{entry.content}</ReactMarkdown>
          </div>
          {entry.tags && entry.tags.length > 0 && (
            <div className="flex gap-1 mt-1">
              {entry.tags.map((tag: string) => (
                <span key={tag} className="text-[10px] bg-green-50 text-green-700 px-1.5 py-0.5 rounded">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const SourceCard = ({ source }: { source: import('../types').PlantDataSource }): React.ReactElement => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-gray-50 rounded-lg p-3 text-sm">
      <div className="flex items-center justify-between">
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
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-gray-500 hover:text-gray-700 underline"
          >
            {expanded ? 'Hide raw data' : 'Show raw data'}
          </button>
        </div>
      </div>
      {source.notes && <p className="text-xs text-gray-500 mt-1">{source.notes}</p>}
      <p className="text-xs text-gray-400 mt-1">
        Ingested: {new Date(source.ingested_at).toLocaleDateString()}
      </p>
      {expanded && (
        <pre className="mt-2 p-3 bg-gray-900 text-green-400 text-xs rounded overflow-x-auto max-h-80">
          {JSON.stringify(source.raw_data, null, 2)}
        </pre>
      )}
    </div>
  );
};

export const PlantsPage = (): React.ReactElement => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingPlant, setEditingPlant] = useState<PlantSpecies | null>(null);
  const [form, setForm] = useState<PlantFormData>(EMPTY_FORM);

  const { data, isLoading } = usePlants({ search: search || undefined });
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

      {isLoading ? (
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
                        onClick={(e) => { e.stopPropagation(); deletePlant.mutate(plant.id); }}
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

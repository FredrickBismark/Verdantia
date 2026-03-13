import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Filter } from 'lucide-react';
import { useGardenStore } from '../stores/gardenStore';
import { journalApi } from '../api/journal';
import { JournalEntryForm } from '../components/JournalEntryForm';
import { JournalFeed } from '../components/JournalFeed';
import type { JournalEntry } from '../api/journal';

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'observation', label: 'Observation' },
  { value: 'pest_issue', label: 'Pest Issue' },
  { value: 'disease_issue', label: 'Disease' },
  { value: 'milestone', label: 'Milestone' },
  { value: 'weather_note', label: 'Weather' },
  { value: 'soil_note', label: 'Soil' },
  { value: 'general', label: 'General' },
  { value: 'harvest_note', label: 'Harvest' },
];

export const JournalPage = (): React.ReactElement => {
  const { selectedGardenId } = useGardenStore();
  const [showForm, setShowForm] = useState(false);
  const [editEntry, setEditEntry] = useState<JournalEntry | null>(null);
  const [filterCategory, setFilterCategory] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['journal', selectedGardenId, filterCategory],
    queryFn: () =>
      journalApi.list(selectedGardenId!, {
        limit: 50,
        category: filterCategory || undefined,
      }),
    enabled: selectedGardenId !== null,
  });

  const entries = data?.data ?? [];

  if (!selectedGardenId) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Journal</h1>
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          Select a garden to view journal entries.
        </div>
      </div>
    );
  }

  const handleEdit = (entry: JournalEntry): void => {
    setEditEntry(entry);
    setShowForm(true);
  };

  const handleClose = (): void => {
    setShowForm(false);
    setEditEntry(null);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Journal</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters((s) => !s)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              showFilters || filterCategory
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Filter className="w-4 h-4" />
            Filter
          </button>
          <button
            onClick={() => {
              setEditEntry(null);
              setShowForm(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Entry
          </button>
        </div>
      </div>

      {showFilters && (
        <div className="bg-white border border-gray-200 rounded-lg p-3 mb-4 flex gap-3 items-center">
          <label className="text-xs font-medium text-gray-600">Category:</label>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          {filterCategory && (
            <button
              onClick={() => setFilterCategory('')}
              className="text-xs text-gray-500 hover:text-gray-700 underline"
            >
              Clear
            </button>
          )}
        </div>
      )}

      {showForm && (
        <div className="mb-6">
          <JournalEntryForm
            gardenId={selectedGardenId}
            onClose={handleClose}
            editEntry={editEntry ?? undefined}
          />
        </div>
      )}

      {isLoading ? (
        <div className="text-gray-500 text-sm">Loading journal entries...</div>
      ) : (
        <JournalFeed entries={entries} onEdit={handleEdit} />
      )}

      {data && data.count > entries.length && (
        <div className="text-center mt-4 text-sm text-gray-500">
          Showing {entries.length} of {data.count} entries
        </div>
      )}
    </div>
  );
};

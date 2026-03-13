import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, X } from 'lucide-react';
import { journalApi } from '../api/journal';
import { plantingsApi } from '../api/plantings';
import type { JournalEntryCreate } from '../api/journal';

const CATEGORIES = [
  { value: 'observation', label: 'Observation' },
  { value: 'pest_issue', label: 'Pest Issue' },
  { value: 'disease_issue', label: 'Disease Issue' },
  { value: 'milestone', label: 'Milestone' },
  { value: 'weather_note', label: 'Weather Note' },
  { value: 'soil_note', label: 'Soil Note' },
  { value: 'general', label: 'General' },
  { value: 'harvest_note', label: 'Harvest Note' },
];

const MOODS = [
  { value: 'great', label: 'Great', color: 'bg-green-100 text-green-700' },
  { value: 'good', label: 'Good', color: 'bg-lime-100 text-lime-700' },
  { value: 'okay', label: 'Okay', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'concerned', label: 'Concerned', color: 'bg-orange-100 text-orange-700' },
  { value: 'bad', label: 'Bad', color: 'bg-red-100 text-red-700' },
];

interface JournalEntryFormProps {
  gardenId: number;
  onClose: () => void;
  editEntry?: {
    id: number;
    planting_id: number | null;
    entry_date: string;
    category: string;
    content: string;
    tags: string[] | null;
    mood: string | null;
  };
}

export const JournalEntryForm = ({ gardenId, onClose, editEntry }: JournalEntryFormProps): React.ReactElement => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<JournalEntryCreate>({
    planting_id: editEntry?.planting_id ?? null,
    entry_date: editEntry?.entry_date ?? new Date().toISOString().split('T')[0],
    category: editEntry?.category ?? 'observation',
    content: editEntry?.content ?? '',
    tags: editEntry?.tags ?? null,
    mood: editEntry?.mood ?? null,
  });
  const [tagInput, setTagInput] = useState('');

  const { data: plantingsData } = useQuery({
    queryKey: ['plantings', gardenId],
    queryFn: () => plantingsApi.list(gardenId, { limit: 100 }),
  });
  const plantings = plantingsData?.data ?? [];

  const createMutation = useMutation({
    mutationFn: (data: JournalEntryCreate) => journalApi.create(gardenId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['journal'] });
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: JournalEntryCreate) => journalApi.update(editEntry!.id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['journal'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!form.content.trim()) return;
    if (editEntry) {
      updateMutation.mutate(form);
    } else {
      createMutation.mutate(form);
    }
  };

  const addTag = (): void => {
    const tag = tagInput.trim();
    if (tag && !(form.tags ?? []).includes(tag)) {
      setForm({ ...form, tags: [...(form.tags ?? []), tag] });
      setTagInput('');
    }
  };

  const removeTag = (tag: string): void => {
    const newTags = (form.tags ?? []).filter((t) => t !== tag);
    setForm({ ...form, tags: newTags.length > 0 ? newTags : null });
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">
          {editEntry ? 'Edit Journal Entry' : 'New Journal Entry'}
        </h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X className="w-4 h-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Date</label>
            <input
              type="date"
              value={form.entry_date}
              onChange={(e) => setForm({ ...form, entry_date: e.target.value })}
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
            <select
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Planting (optional)</label>
            <select
              value={form.planting_id ?? ''}
              onChange={(e) => setForm({ ...form, planting_id: e.target.value ? parseInt(e.target.value) : null })}
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
            >
              <option value="">None</option>
              {plantings.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.bed_or_location ?? `Planting #${p.id}`}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Mood</label>
            <div className="flex gap-1 pt-0.5">
              {MOODS.map((m) => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => setForm({ ...form, mood: form.mood === m.value ? null : m.value })}
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                    form.mood === m.value ? m.color : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Content</label>
          <textarea
            rows={4}
            value={form.content}
            onChange={(e) => setForm({ ...form, content: e.target.value })}
            placeholder="Write your observation or note... (Markdown supported)"
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:ring-1 focus:ring-green-400"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Tags</label>
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addTag();
                }
              }}
              placeholder="Add tag..."
              className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
            />
            <button
              type="button"
              onClick={addTag}
              className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
            >
              Add
            </button>
          </div>
          {form.tags && form.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {form.tags.map((tag) => (
                <span key={tag} className="flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 rounded-full text-xs">
                  {tag}
                  <button type="button" onClick={() => removeTag(tag)} className="hover:text-green-900">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={isPending || !form.content.trim()}
            className="px-4 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
            ) : editEntry ? (
              'Update Entry'
            ) : (
              'Add Entry'
            )}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

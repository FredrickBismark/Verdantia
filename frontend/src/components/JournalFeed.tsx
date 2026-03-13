import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Pencil, Trash2, Bug, Leaf, Cloud, FlaskConical, Star, Eye, Wheat, FileText } from 'lucide-react';
import { journalApi } from '../api/journal';
import type { JournalEntry } from '../api/journal';

const CATEGORY_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  observation: { icon: Eye, color: 'bg-blue-100 text-blue-700', label: 'Observation' },
  pest_issue: { icon: Bug, color: 'bg-red-100 text-red-700', label: 'Pest Issue' },
  disease_issue: { icon: Bug, color: 'bg-orange-100 text-orange-700', label: 'Disease' },
  milestone: { icon: Star, color: 'bg-purple-100 text-purple-700', label: 'Milestone' },
  weather_note: { icon: Cloud, color: 'bg-sky-100 text-sky-700', label: 'Weather' },
  soil_note: { icon: FlaskConical, color: 'bg-amber-100 text-amber-700', label: 'Soil' },
  general: { icon: FileText, color: 'bg-gray-100 text-gray-700', label: 'General' },
  harvest_note: { icon: Wheat, color: 'bg-green-100 text-green-700', label: 'Harvest' },
};

const MOOD_LABELS: Record<string, string> = {
  great: 'Great',
  good: 'Good',
  okay: 'Okay',
  concerned: 'Concerned',
  bad: 'Bad',
};

interface JournalFeedProps {
  entries: JournalEntry[];
  onEdit: (entry: JournalEntry) => void;
}

export const JournalFeed = ({ entries, onEdit }: JournalFeedProps): React.ReactElement => {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: (id: number) => journalApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['journal'] });
    },
  });

  if (entries.length === 0) {
    return (
      <div className="text-center py-8">
        <Leaf className="w-10 h-10 text-gray-300 mx-auto mb-2" />
        <p className="text-sm text-gray-400">No journal entries yet.</p>
      </div>
    );
  }

  // Group entries by date
  const grouped: Record<string, JournalEntry[]> = {};
  for (const entry of entries) {
    const dateKey = entry.entry_date;
    if (!grouped[dateKey]) grouped[dateKey] = [];
    grouped[dateKey].push(entry);
  }

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([dateStr, dateEntries]) => (
        <div key={dateStr}>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            {new Date(dateStr + 'T00:00:00').toLocaleDateString(undefined, {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </h3>
          <div className="space-y-2">
            {dateEntries.map((entry) => {
              const config = CATEGORY_CONFIG[entry.category] ?? CATEGORY_CONFIG.general;
              const Icon = config.icon;
              return (
                <div key={entry.id} className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <div className={`p-1.5 rounded-lg ${config.color}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
                            {config.label}
                          </span>
                          {entry.mood && (
                            <span className="text-xs text-gray-400">
                              Mood: {MOOD_LABELS[entry.mood] ?? entry.mood}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-800 whitespace-pre-line">{entry.content}</p>
                        {entry.tags && entry.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {entry.tags.map((tag) => (
                              <span key={tag} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-1 ml-2">
                      <button
                        onClick={() => onEdit(entry)}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => deleteMutation.mutate(entry.id)}
                        className="p-1 text-gray-400 hover:text-red-600 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

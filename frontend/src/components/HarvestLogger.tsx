import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Star } from 'lucide-react';
import { harvestsApi } from '../api/harvests';
import type { HarvestCreate } from '../api/harvests';

const UNITS = ['kg', 'lbs', 'count', 'bunches', 'liters'];

interface HarvestLoggerProps {
  plantingId: number;
}

export const HarvestLogger = ({ plantingId }: HarvestLoggerProps): React.ReactElement => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<HarvestCreate>({
    harvest_date: new Date().toISOString().split('T')[0],
    quantity: 0,
    unit: 'kg',
    quality_rating: null,
    notes: null,
  });
  const [hoverRating, setHoverRating] = useState(0);

  const logMutation = useMutation({
    mutationFn: (data: HarvestCreate) => harvestsApi.log(plantingId, data),
    onSuccess: () => {
      setForm({
        harvest_date: new Date().toISOString().split('T')[0],
        quantity: 0,
        unit: 'kg',
        quality_rating: null,
        notes: null,
      });
      void queryClient.invalidateQueries({ queryKey: ['harvests', plantingId] });
      void queryClient.invalidateQueries({ queryKey: ['harvest-stats', plantingId] });
    },
  });

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (form.quantity <= 0) return;
    logMutation.mutate(form);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <h4 className="text-sm font-semibold text-gray-700">Log Harvest</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Date</label>
          <input
            type="date"
            value={form.harvest_date}
            onChange={(e) => setForm({ ...form, harvest_date: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Quantity</label>
          <input
            type="number"
            step="0.1"
            min="0"
            value={form.quantity || ''}
            onChange={(e) => setForm({ ...form, quantity: parseFloat(e.target.value) || 0 })}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Unit</label>
          <select
            value={form.unit}
            onChange={(e) => setForm({ ...form, unit: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
          >
            {UNITS.map((u) => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Quality</label>
          <div className="flex gap-0.5 pt-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setForm({ ...form, quality_rating: form.quality_rating === star ? null : star })}
                className="p-0.5"
              >
                <Star
                  className={`w-5 h-5 ${
                    star <= (hoverRating || form.quality_rating || 0)
                      ? 'text-amber-400 fill-amber-400'
                      : 'text-gray-300'
                  }`}
                />
              </button>
            ))}
          </div>
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
        <textarea
          rows={2}
          value={form.notes ?? ''}
          onChange={(e) => setForm({ ...form, notes: e.target.value || null })}
          placeholder="Any notes about this harvest..."
          className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:ring-1 focus:ring-green-400"
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={logMutation.isPending || form.quantity <= 0}
          className="px-4 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
        >
          {logMutation.isPending ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
          ) : (
            'Log Harvest'
          )}
        </button>
        {logMutation.isError && (
          <span className="text-sm text-red-600">{logMutation.error.message}</span>
        )}
        {logMutation.isSuccess && (
          <span className="text-sm text-green-600">Harvest logged!</span>
        )}
      </div>
    </form>
  );
};

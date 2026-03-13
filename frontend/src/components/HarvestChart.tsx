import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loader2 } from 'lucide-react';
import { harvestsApi } from '../api/harvests';
import type { HarvestLog } from '../types';

interface HarvestChartProps {
  plantingId: number;
}

export const HarvestChart = ({ plantingId }: HarvestChartProps): React.ReactElement => {
  const { data, isLoading } = useQuery({
    queryKey: ['harvests', plantingId],
    queryFn: () => harvestsApi.list(plantingId, 0, 100),
  });

  const harvests: HarvestLog[] = data?.data ?? [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-gray-400">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  if (harvests.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-6">No harvest data to chart yet.</p>
    );
  }

  const chartData = harvests
    .sort((a, b) => a.harvest_date.localeCompare(b.harvest_date))
    .map((h) => ({
      date: h.harvest_date,
      quantity: h.quantity,
      unit: h.unit,
    }));

  const unit = chartData[0]?.unit ?? '';

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h4 className="text-sm font-semibold text-gray-700 mb-3">Harvest Over Time</h4>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            tickFormatter={(v: string) => {
              const d = new Date(v);
              return `${d.getMonth() + 1}/${d.getDate()}`;
            }}
          />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            labelFormatter={(v: string) => new Date(v).toLocaleDateString()}
            formatter={(value: number) => [`${value} ${unit}`, 'Quantity']}
          />
          <Bar dataKey="quantity" fill="#16a34a" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, Thermometer, Droplets, Wind, Eye, AlertTriangle, Sprout } from 'lucide-react';
import { useGardenStore } from '../stores/gardenStore';
import { weatherApi } from '../api/weather';
import type { WeatherRecord } from '../types';

export const WeatherPage = (): React.ReactElement => {
  const { selectedGardenId } = useGardenStore();
  const queryClient = useQueryClient();
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  const { data: currentData, isLoading: loadingCurrent } = useQuery({
    queryKey: ['weather', 'current', selectedGardenId],
    queryFn: () => weatherApi.current(selectedGardenId!),
    enabled: selectedGardenId !== null,
  });

  const { data: forecastData, isLoading: loadingForecast } = useQuery({
    queryKey: ['weather', 'forecast', selectedGardenId],
    queryFn: () => weatherApi.forecast(selectedGardenId!, 7),
    enabled: selectedGardenId !== null,
  });

  const { data: frostData } = useQuery({
    queryKey: ['weather', 'frost', selectedGardenId],
    queryFn: () => weatherApi.frostDates(selectedGardenId!),
    enabled: selectedGardenId !== null,
  });

  const { data: gddData } = useQuery({
    queryKey: ['weather', 'gdd', selectedGardenId],
    queryFn: () => weatherApi.gdd(selectedGardenId!),
    enabled: selectedGardenId !== null,
  });

  const syncMutation = useMutation({
    mutationFn: () => weatherApi.sync(selectedGardenId!),
    onSuccess: (res) => {
      setSyncMsg(`Synced ${res.data.synced} records`);
      void queryClient.invalidateQueries({ queryKey: ['weather'] });
      setTimeout(() => setSyncMsg(null), 3000);
    },
  });

  if (!selectedGardenId) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Weather</h1>
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          Select a garden to view weather data.
        </div>
      </div>
    );
  }

  const current = currentData?.data ?? null;
  const forecast = forecastData?.data ?? [];
  const frost = frostData?.data ?? null;
  const gdd = gddData?.data ?? null;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Weather</h1>
        <button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
        >
          <RefreshCw size={14} className={syncMutation.isPending ? 'animate-spin' : ''} />
          Sync Weather
        </button>
      </div>

      {syncMsg && (
        <div className="mb-4 px-4 py-2 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">
          {syncMsg}
        </div>
      )}

      {/* Current conditions */}
      <section className="mb-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-3">Current Conditions</h2>
        {loadingCurrent ? (
          <div className="bg-white rounded-lg border p-6 text-gray-400 text-sm">Loading…</div>
        ) : current ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={<Thermometer size={18} className="text-orange-500" />}
              label="Temperature"
              value={current.temp_c !== null ? `${current.temp_c.toFixed(1)}°C` : '—'}
              warn={current.frost_risk ?? false}
            />
            <StatCard
              icon={<Droplets size={18} className="text-blue-500" />}
              label="Humidity"
              value={current.humidity_pct !== null ? `${current.humidity_pct.toFixed(0)}%` : '—'}
            />
            <StatCard
              icon={<Wind size={18} className="text-teal-500" />}
              label="Wind"
              value={current.wind_speed_kmh !== null ? `${current.wind_speed_kmh.toFixed(0)} km/h` : '—'}
            />
            <StatCard
              icon={<Eye size={18} className="text-indigo-500" />}
              label="Cloud Cover"
              value={current.cloud_cover_pct !== null ? `${current.cloud_cover_pct.toFixed(0)}%` : '—'}
            />
          </div>
        ) : (
          <div className="bg-white rounded-lg border p-6 text-gray-400 text-sm">
            No data yet — click Sync Weather.
          </div>
        )}
      </section>

      {/* Frost dates & GDD */}
      <section className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={16} className="text-pink-500" />
            <h3 className="font-semibold text-gray-700">Frost Dates</h3>
          </div>
          {frost ? (
            frost.last_spring_frost ? (
              <dl className="space-y-1 text-sm text-gray-600">
                <div className="flex justify-between">
                  <dt>Last spring frost</dt>
                  <dd className="font-medium">{frost.last_spring_frost}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>First fall frost</dt>
                  <dd className="font-medium">{frost.first_fall_frost ?? '—'}</dd>
                </div>
                {frost.growing_season_days !== null && (
                  <div className="flex justify-between">
                    <dt>Growing season</dt>
                    <dd className="font-medium">{frost.growing_season_days} days</dd>
                  </div>
                )}
              </dl>
            ) : (
              <p className="text-sm text-gray-400">{frost.note ?? 'Sync more weather data to estimate.'}</p>
            )
          ) : (
            <p className="text-sm text-gray-400">Loading…</p>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Sprout size={16} className="text-green-600" />
            <h3 className="font-semibold text-gray-700">Growing Degree Days</h3>
          </div>
          {gdd ? (
            <dl className="space-y-1 text-sm text-gray-600">
              <div className="flex justify-between">
                <dt>Accumulated (since {gdd.start_date})</dt>
                <dd className="font-medium text-green-700">{gdd.total_gdd.toFixed(0)} GDD</dd>
              </div>
              <div className="flex justify-between">
                <dt>Base temperature</dt>
                <dd className="font-medium">{gdd.base_temp_c}°C</dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-gray-400">No data yet.</p>
          )}
        </div>
      </section>

      {/* 7-day forecast */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-3">7-Day Forecast</h2>
        {loadingForecast ? (
          <div className="bg-white rounded-lg border p-6 text-gray-400 text-sm">Loading…</div>
        ) : forecast.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
            {forecast.map((day) => (
              <ForecastCard key={day.id} day={day} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg border p-6 text-gray-400 text-sm">
            No forecast data — click Sync Weather.
          </div>
        )}
      </section>
    </div>
  );
};

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  warn?: boolean;
}

const StatCard = ({ icon, label, value, warn }: StatCardProps): React.ReactElement => (
  <div className={`bg-white rounded-lg border p-4 flex flex-col gap-2 ${warn ? 'border-pink-300 bg-pink-50' : 'border-gray-200'}`}>
    <div className="flex items-center gap-1.5 text-xs text-gray-500">
      {icon}
      {label}
      {warn && <AlertTriangle size={12} className="text-pink-500 ml-auto" />}
    </div>
    <span className="text-2xl font-semibold text-gray-800">{value}</span>
  </div>
);

const ForecastCard = ({ day }: { day: WeatherRecord }): React.ReactElement => {
  const dateStr = new Date(day.timestamp).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  return (
    <div className={`bg-white rounded-lg border p-3 text-center text-xs ${day.frost_risk ? 'border-pink-200 bg-pink-50' : 'border-gray-200'}`}>
      <div className="font-medium text-gray-600 mb-1">{dateStr}</div>
      {day.temp_max_c !== null && (
        <div className="text-base font-bold text-gray-800">{day.temp_max_c.toFixed(0)}°</div>
      )}
      {day.temp_min_c !== null && (
        <div className="text-gray-400">{day.temp_min_c.toFixed(0)}°</div>
      )}
      {day.precipitation_mm !== null && day.precipitation_mm > 0 && (
        <div className="text-blue-500 mt-1">{day.precipitation_mm.toFixed(0)}mm</div>
      )}
      {day.frost_risk && (
        <div className="text-pink-500 mt-1 font-medium">Frost</div>
      )}
    </div>
  );
};

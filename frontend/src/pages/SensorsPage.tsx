import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  Thermometer,
  Droplets,
  Wind,
  Plus,
  RefreshCw,
  Loader2,
  Radio,
  CircleDot,
} from 'lucide-react';
import { useGardenStore } from '../stores/gardenStore';
import { sensorsApi } from '../api/sensors';
import type { SensorInfo, SensorStatus, SensorReadingCreate } from '../api/sensors';
import type { SensorReading } from '../types';

const SENSOR_TYPE_ICONS: Record<string, typeof Thermometer> = {
  temperature: Thermometer,
  humidity: Droplets,
  soil_moisture: Droplets,
  wind: Wind,
};

const HEALTH_COLORS: Record<string, string> = {
  active: 'text-green-600 bg-green-50',
  idle: 'text-yellow-600 bg-yellow-50',
  stale: 'text-red-600 bg-red-50',
  unknown: 'text-gray-500 bg-gray-50',
};

export const SensorsPage = (): React.ReactElement => {
  const { selectedGardenId } = useGardenStore();
  const queryClient = useQueryClient();
  const [selectedSensor, setSelectedSensor] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  const { data: sensorsData, isLoading: sensorsLoading } = useQuery({
    queryKey: ['sensors', selectedGardenId],
    queryFn: () => sensorsApi.list(selectedGardenId!),
    enabled: !!selectedGardenId,
  });

  const { data: statusData } = useQuery({
    queryKey: ['sensors-status', selectedGardenId],
    queryFn: () => sensorsApi.status(selectedGardenId!),
    enabled: !!selectedGardenId,
    refetchInterval: 30_000,
  });

  const { data: readingsData, isLoading: readingsLoading } = useQuery({
    queryKey: ['sensor-readings', selectedGardenId, selectedSensor],
    queryFn: () => sensorsApi.readings(selectedGardenId!, selectedSensor!, 50),
    enabled: !!selectedGardenId && !!selectedSensor,
  });

  const sensors = sensorsData?.data ?? [];
  const statuses = statusData?.data ?? [];
  const readings = readingsData?.data ?? [];

  const statusMap = new Map(statuses.map((s) => [s.sensor_id, s]));

  if (!selectedGardenId) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Select a garden to view sensors.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sensors</h1>
          <p className="text-sm text-gray-500 mt-1">
            {sensors.length} sensor{sensors.length !== 1 ? 's' : ''} registered
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['sensors', selectedGardenId] });
              queryClient.invalidateQueries({ queryKey: ['sensors-status', selectedGardenId] });
            }}
            className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Plus className="w-4 h-4" />
            Add Reading
          </button>
        </div>
      </div>

      {showAddForm && (
        <AddReadingForm
          gardenId={selectedGardenId}
          onClose={() => setShowAddForm(false)}
        />
      )}

      {sensorsLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : sensors.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Radio className="w-12 h-12 mx-auto text-gray-300 mb-3" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No sensors yet</h3>
          <p className="text-sm text-gray-500">
            Add manual readings or connect MQTT sensors to get started.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Sensor List
            </h2>
            {sensors.map((sensor) => {
              const status = statusMap.get(sensor.sensor_id);
              const Icon = SENSOR_TYPE_ICONS[sensor.sensor_type] ?? Activity;
              const healthClass = HEALTH_COLORS[status?.health ?? 'unknown'];
              const isSelected = selectedSensor === sensor.sensor_id;

              return (
                <button
                  key={sensor.sensor_id}
                  onClick={() => setSelectedSensor(sensor.sensor_id)}
                  className={`w-full text-left p-4 rounded-lg border transition-colors ${
                    isSelected
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5 text-gray-600" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 truncate">
                        {sensor.sensor_id}
                      </div>
                      <div className="text-xs text-gray-500">
                        {sensor.sensor_type} &middot; {sensor.reading_count} readings
                      </div>
                    </div>
                    {status && (
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full ${healthClass}`}
                      >
                        {status.health}
                      </span>
                    )}
                  </div>
                  {sensor.location && (
                    <div className="text-xs text-gray-400 mt-1">{sensor.location}</div>
                  )}
                </button>
              );
            })}
          </div>

          <div className="lg:col-span-2">
            {selectedSensor ? (
              <SensorDetail
                sensorId={selectedSensor}
                sensor={sensors.find((s) => s.sensor_id === selectedSensor)}
                status={statusMap.get(selectedSensor)}
                readings={readings}
                isLoading={readingsLoading}
              />
            ) : (
              <div className="flex items-center justify-center h-64 bg-white rounded-lg border border-gray-200 text-gray-500">
                Select a sensor to view details
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const SensorDetail = ({
  sensorId,
  sensor,
  status,
  readings,
  isLoading,
}: {
  sensorId: string;
  sensor: SensorInfo | undefined;
  status: SensorStatus | undefined;
  readings: SensorReading[];
  isLoading: boolean;
}): React.ReactElement => {
  const healthClass = HEALTH_COLORS[status?.health ?? 'unknown'];
  const latestReading = readings[0];

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">{sensorId}</h2>
          {status && (
            <span className={`text-sm font-medium px-3 py-1 rounded-full ${healthClass}`}>
              {status.connected && <CircleDot className="w-3 h-3 inline mr-1" />}
              {status.health}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-gray-500">Type</div>
            <div className="font-medium">{sensor?.sensor_type ?? '—'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Location</div>
            <div className="font-medium">{sensor?.location ?? '—'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Source</div>
            <div className="font-medium">{sensor?.source ?? '—'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Total Readings</div>
            <div className="font-medium">{sensor?.reading_count ?? 0}</div>
          </div>
        </div>

        {latestReading && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-500 mb-1">Latest Reading</div>
            <div className="text-2xl font-bold text-gray-900">
              {latestReading.value} <span className="text-sm font-normal text-gray-500">{latestReading.unit}</span>
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {new Date(latestReading.timestamp).toLocaleString()}
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Recent Readings</h3>
        {isLoading ? (
          <div className="flex items-center justify-center h-24">
            <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
          </div>
        ) : readings.length === 0 ? (
          <p className="text-sm text-gray-500">No readings recorded.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 font-medium">Time</th>
                  <th className="pb-2 font-medium">Value</th>
                  <th className="pb-2 font-medium">Unit</th>
                </tr>
              </thead>
              <tbody>
                {readings.slice(0, 20).map((r) => (
                  <tr key={r.id} className="border-b border-gray-50">
                    <td className="py-2 text-gray-600">
                      {new Date(r.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2 font-medium">{r.value}</td>
                    <td className="py-2 text-gray-500">{r.unit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

const AddReadingForm = ({
  gardenId,
  onClose,
}: {
  gardenId: number;
  onClose: () => void;
}): React.ReactElement => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<SensorReadingCreate>({
    sensor_id: '',
    sensor_type: 'temperature',
    value: 0,
    unit: '',
  });

  const mutation = useMutation({
    mutationFn: (data: SensorReadingCreate) => sensorsApi.addReading(gardenId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sensors', gardenId] });
      queryClient.invalidateQueries({ queryKey: ['sensors-status', gardenId] });
      queryClient.invalidateQueries({ queryKey: ['sensor-readings', gardenId] });
      onClose();
    },
  });

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Add Manual Reading</h3>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate(form);
        }}
        className="grid grid-cols-2 sm:grid-cols-5 gap-3"
      >
        <input
          type="text"
          placeholder="Sensor ID"
          value={form.sensor_id}
          onChange={(e) => setForm({ ...form, sensor_id: e.target.value })}
          required
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        />
        <select
          value={form.sensor_type}
          onChange={(e) => setForm({ ...form, sensor_type: e.target.value })}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="temperature">Temperature</option>
          <option value="humidity">Humidity</option>
          <option value="soil_moisture">Soil Moisture</option>
          <option value="light">Light</option>
          <option value="wind">Wind</option>
          <option value="rain">Rain</option>
        </select>
        <input
          type="number"
          step="any"
          placeholder="Value"
          value={form.value || ''}
          onChange={(e) => setForm({ ...form, value: parseFloat(e.target.value) || 0 })}
          required
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        />
        <input
          type="text"
          placeholder="Unit (e.g. °C)"
          value={form.unit}
          onChange={(e) => setForm({ ...form, unit: e.target.value })}
          required
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        />
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {mutation.isPending ? 'Saving...' : 'Save'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
      {mutation.isError && (
        <p className="mt-2 text-sm text-red-600">{(mutation.error as Error).message}</p>
      )}
    </div>
  );
};

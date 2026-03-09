import { useNavigate } from 'react-router-dom';
import { MapPin, Sprout, Leaf, Plus } from 'lucide-react';
import { useGardens } from '../hooks/useGardens';
import { usePlants } from '../hooks/usePlants';
import { usePlantings } from '../hooks/usePlantings';
import { useGardenStore } from '../stores/gardenStore';

export const DashboardPage = (): React.ReactElement => {
  const navigate = useNavigate();
  const { data: gardensData, isLoading: gardensLoading } = useGardens();
  const { data: plantsData } = usePlants();
  const { selectedGardenId, setSelectedGardenId } = useGardenStore();
  const { data: plantingsData } = usePlantings(selectedGardenId);

  const gardens = gardensData?.data ?? [];
  const totalPlants = plantsData?.count ?? 0;
  const plantings = plantingsData?.data ?? [];
  const activePlantings = plantings.filter((p) => p.status === 'active' || p.status === 'planted');

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div
          onClick={() => navigate('/gardens')}
          className="bg-white rounded-lg border border-gray-200 p-5 cursor-pointer hover:border-green-300 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
              <MapPin className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{gardens.length}</p>
              <p className="text-sm text-gray-500">Gardens</p>
            </div>
          </div>
        </div>
        <div
          onClick={() => navigate('/plants')}
          className="bg-white rounded-lg border border-gray-200 p-5 cursor-pointer hover:border-green-300 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center">
              <Sprout className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{totalPlants}</p>
              <p className="text-sm text-gray-500">Plant Species</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-lime-50 rounded-lg flex items-center justify-center">
              <Leaf className="w-5 h-5 text-lime-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{activePlantings.length}</p>
              <p className="text-sm text-gray-500">Active Plantings</p>
            </div>
          </div>
        </div>
      </div>

      {gardensLoading ? (
        <div className="text-gray-500 text-sm">Loading...</div>
      ) : gardens.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Welcome to Verdanta</h3>
          <p className="text-gray-500 text-sm mb-4">Create your first garden to get started.</p>
          <button
            onClick={() => navigate('/gardens')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
          >
            Create Garden
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900">Your Gardens</h2>
              <button
                onClick={() => navigate('/gardens')}
                className="text-sm text-green-600 hover:text-green-700 font-medium"
              >
                Manage
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {gardens.map((garden) => (
                <div
                  key={garden.id}
                  onClick={() => setSelectedGardenId(garden.id)}
                  className={`bg-white rounded-lg border p-4 cursor-pointer transition-colors ${
                    selectedGardenId === garden.id
                      ? 'border-green-500 ring-2 ring-green-100'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <h3 className="font-medium text-gray-900">{garden.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {garden.latitude.toFixed(2)}, {garden.longitude.toFixed(2)}
                    {garden.usda_zone ? ` | Zone ${garden.usda_zone}` : ''}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {selectedGardenId && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold text-gray-900">Plantings</h2>
                <button
                  onClick={() => navigate('/gardens')}
                  className="flex items-center gap-1 text-sm text-green-600 hover:text-green-700 font-medium"
                >
                  <Plus className="w-4 h-4" /> Add Planting
                </button>
              </div>
              {plantings.length === 0 ? (
                <div className="bg-white rounded-lg border border-gray-200 p-6 text-center text-gray-500 text-sm">
                  No plantings in this garden yet.
                </div>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 bg-gray-50">
                        <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Location</th>
                        <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase">Qty</th>
                        <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase hidden md:table-cell">Seeded</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {plantings.map((p) => (
                        <tr key={p.id} className="hover:bg-gray-50">
                          <td className="px-4 py-2 text-sm text-gray-900">{p.bed_or_location ?? '-'}</td>
                          <td className="px-4 py-2">
                            <StatusBadge status={p.status} />
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-600">{p.quantity}</td>
                          <td className="px-4 py-2 text-sm text-gray-600 hidden md:table-cell">{p.date_seeded ?? '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const StatusBadge = ({ status }: { status: string }): React.ReactElement => {
  const colors: Record<string, string> = {
    planned: 'bg-blue-100 text-blue-700',
    planted: 'bg-green-100 text-green-700',
    active: 'bg-green-100 text-green-700',
    harvesting: 'bg-amber-100 text-amber-700',
    completed: 'bg-gray-100 text-gray-600',
    removed: 'bg-red-100 text-red-600',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  );
};

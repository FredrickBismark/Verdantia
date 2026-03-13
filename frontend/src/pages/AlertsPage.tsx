import { Bell } from 'lucide-react';
import { useGardenStore } from '../stores/gardenStore';
import { AlertPanel } from '../components/AlertPanel';

export const AlertsPage = (): React.ReactElement => {
  const { selectedGardenId } = useGardenStore();

  if (!selectedGardenId) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Alerts</h1>
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          Select a garden to view alerts.
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-6">
        <Bell size={20} className="text-orange-500" />
        <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
      </div>
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <AlertPanel gardenId={selectedGardenId} />
      </div>
    </div>
  );
};

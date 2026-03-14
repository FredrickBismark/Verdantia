import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  Check,
  CloudRain,
  Eye,
  Snowflake,
  Sprout,
  Thermometer,
  X,
} from 'lucide-react';
import { alertsApi } from '../api/alerts';
import type { Alert } from '../types';

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
};

const TYPE_ICONS: Record<string, React.ReactElement> = {
  frost: <Snowflake size={16} className="text-blue-500" />,
  extreme_weather: <Thermometer size={16} className="text-red-500" />,
  watering: <CloudRain size={16} className="text-cyan-500" />,
  harvest: <Sprout size={16} className="text-green-500" />,
  pest: <AlertTriangle size={16} className="text-yellow-600" />,
  disease: <AlertTriangle size={16} className="text-orange-500" />,
  general: <Eye size={16} className="text-gray-500" />,
};

interface AlertPanelProps {
  gardenId: number;
  compact?: boolean;
}

export const AlertPanel = ({ gardenId, compact = false }: AlertPanelProps): React.ReactElement => {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['alerts', gardenId],
    queryFn: () => alertsApi.list(gardenId),
    refetchInterval: 60_000,
  });

  const checkMutation = useMutation({
    mutationFn: () => alertsApi.check(gardenId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['alerts', gardenId] });
    },
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: number) => alertsApi.acknowledge(alertId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['alerts', gardenId] });
    },
  });

  const dismissMutation = useMutation({
    mutationFn: (alertId: number) => alertsApi.dismiss(alertId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['alerts', gardenId] });
    },
  });

  const alerts: Alert[] = data?.data ?? [];
  const activeAlerts = alerts.filter((a) => !a.dismissed);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2">
        <div className="h-12 bg-gray-100 rounded-lg" />
        <div className="h-12 bg-gray-100 rounded-lg" />
      </div>
    );
  }

  if (activeAlerts.length === 0 && compact) {
    return (
      <p className="text-sm text-gray-400 text-center py-2">No active alerts</p>
    );
  }

  return (
    <div className="space-y-2">
      {!compact && (
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            {activeAlerts.length} active alert{activeAlerts.length !== 1 ? 's' : ''}
          </span>
          <button
            onClick={() => checkMutation.mutate()}
            disabled={checkMutation.isPending}
            className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 text-gray-600 disabled:opacity-50"
          >
            {checkMutation.isPending ? 'Checking…' : 'Refresh alerts'}
          </button>
        </div>
      )}

      {activeAlerts.length === 0 && !compact && (
        <div className="text-center py-6 text-gray-400 text-sm">
          <AlertTriangle size={24} className="mx-auto mb-2 text-gray-300" />
          No active alerts. Your garden is looking good!
        </div>
      )}

      {(compact ? activeAlerts.slice(0, 5) : activeAlerts).map((alert) => (
        <AlertCard
          key={alert.id}
          alert={alert}
          compact={compact}
          onAcknowledge={() => acknowledgeMutation.mutate(alert.id)}
          onDismiss={() => dismissMutation.mutate(alert.id)}
        />
      ))}
    </div>
  );
};

interface AlertCardProps {
  alert: Alert;
  compact: boolean;
  onAcknowledge: () => void;
  onDismiss: () => void;
}

const AlertCard = ({ alert, compact, onAcknowledge, onDismiss }: AlertCardProps): React.ReactElement => {
  const severityClass = SEVERITY_STYLES[alert.severity] ?? SEVERITY_STYLES.medium;
  const icon = TYPE_ICONS[alert.alert_type] ?? TYPE_ICONS.general;

  return (
    <div className={`rounded-lg border p-3 ${severityClass}`}>
      <div className="flex items-start gap-2">
        <div className="mt-0.5 flex-shrink-0">{icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">{alert.title}</span>
            <span className="text-xs opacity-70 flex-shrink-0">
              {new Date(alert.trigger_date).toLocaleDateString()}
            </span>
          </div>
          {!compact && alert.description && (
            <p className="text-xs mt-1 opacity-80">{alert.description}</p>
          )}
          {!compact && (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs opacity-60 capitalize">{alert.source.replace('_', ' ')}</span>
              {!alert.acknowledged && (
                <button
                  onClick={onAcknowledge}
                  className="text-xs flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/50 hover:bg-white/80"
                >
                  <Check size={10} /> Acknowledge
                </button>
              )}
              <button
                onClick={onDismiss}
                className="text-xs flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/50 hover:bg-white/80"
              >
                <X size={10} /> Dismiss
              </button>
            </div>
          )}
        </div>
        {compact && (
          <button
            onClick={onDismiss}
            className="text-xs opacity-50 hover:opacity-100 flex-shrink-0"
          >
            <X size={14} />
          </button>
        )}
      </div>
    </div>
  );
};

export const useAlertCount = (gardenId: number | null): number => {
  const { data } = useQuery({
    queryKey: ['alerts', gardenId],
    queryFn: () => alertsApi.list(gardenId!),
    enabled: gardenId !== null,
    refetchInterval: 60_000,
  });
  return (data?.data ?? []).filter((a: Alert) => !a.dismissed).length;
};

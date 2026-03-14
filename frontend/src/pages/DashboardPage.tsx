import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  MapPin, Sprout, Leaf, Plus, CloudSun, Sun, CloudRain, Snowflake,
  CheckCircle2, Circle, BookOpen, Wheat, Bot, Eye, Loader2,
} from 'lucide-react';
import { useGardens } from '../hooks/useGardens';
import { usePlants } from '../hooks/usePlants';
import { usePlantings } from '../hooks/usePlantings';
import { useGardenStore } from '../stores/gardenStore';
import { weatherApi } from '../api/weather';
import { calendarApi } from '../api/calendar';
import { journalApi } from '../api/journal';
import { AlertPanel } from '../components/AlertPanel';
import { JournalEntryForm } from '../components/JournalEntryForm';
import { HarvestLogger } from '../components/HarvestLogger';
import type { CalendarEvent, WeatherRecord } from '../types';
import type { JournalEntry } from '../api/journal';
import type { FrostDatesResult } from '../api/weather';

export const DashboardPage = (): React.ReactElement => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: gardensData, isLoading: gardensLoading } = useGardens();
  const { data: plantsData } = usePlants();
  const { selectedGardenId, setSelectedGardenId } = useGardenStore();
  const { data: plantingsData } = usePlantings(selectedGardenId);
  const [showJournalForm, setShowJournalForm] = useState(false);
  const [showHarvestForm, setShowHarvestForm] = useState(false);

  const gardens = gardensData?.data ?? [];
  const totalPlants = plantsData?.count ?? 0;
  const plantings = plantingsData?.data ?? [];
  const activePlantings = plantings.filter((p) => p.status === 'active' || p.status === 'planted');

  // Weather data
  const { data: weatherData } = useQuery({
    queryKey: ['weather', 'current', selectedGardenId],
    queryFn: () => weatherApi.current(selectedGardenId!),
    enabled: selectedGardenId !== null,
  });

  const { data: forecastData } = useQuery({
    queryKey: ['weather', 'forecast', selectedGardenId],
    queryFn: () => weatherApi.forecast(selectedGardenId!, 3),
    enabled: selectedGardenId !== null,
  });

  // Today's tasks
  const today = new Date().toISOString().split('T')[0];
  const { data: todayEvents } = useQuery({
    queryKey: ['calendar', 'today', selectedGardenId],
    queryFn: () => calendarApi.listEvents(selectedGardenId!, { start_date: today, end_date: today }),
    enabled: selectedGardenId !== null,
  });

  // Recent journal entries
  const { data: recentJournal } = useQuery({
    queryKey: ['journal', 'recent', selectedGardenId],
    queryFn: () => journalApi.recent(selectedGardenId!, 3),
    enabled: selectedGardenId !== null,
  });

  // Frost dates for season progress
  const { data: frostData } = useQuery({
    queryKey: ['weather', 'frost', selectedGardenId],
    queryFn: () => weatherApi.frostDates(selectedGardenId!),
    enabled: selectedGardenId !== null,
  });

  const completeMutation = useMutation({
    mutationFn: (eventId: number) => calendarApi.completeEvent(eventId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['calendar', 'today'] });
    },
  });

  const currentWeather: WeatherRecord | null = weatherData?.data ?? null;
  const forecast: WeatherRecord[] = forecastData?.data ?? [];
  const todayTasks: CalendarEvent[] = todayEvents?.data ?? [];
  const journalEntries: JournalEntry[] = recentJournal?.data ?? [];
  const frostDates: FrostDatesResult | null = frostData?.data ?? null;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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
          {/* Garden selector */}
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {gardens.map((garden) => (
                <div
                  key={garden.id}
                  onClick={() => setSelectedGardenId(garden.id)}
                  className={`bg-white rounded-lg border p-3 cursor-pointer transition-colors ${
                    selectedGardenId === garden.id
                      ? 'border-green-500 ring-2 ring-green-100'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <h3 className="font-medium text-gray-900 text-sm">{garden.name}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {garden.usda_zone ? `Zone ${garden.usda_zone}` : `${garden.latitude.toFixed(2)}, ${garden.longitude.toFixed(2)}`}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {selectedGardenId && (
            <>
              {/* Weather Widget - full width */}
              <WeatherWidget current={currentWeather} forecast={forecast} />

              {/* Tasks + Journal side by side */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <TodaysTasks
                  tasks={todayTasks}
                  onComplete={(id) => completeMutation.mutate(id)}
                  isPending={completeMutation.isPending}
                />
                <RecentJournal entries={journalEntries} onNavigate={() => navigate('/journal')} />
              </div>

              {/* Alerts widget */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-700">Active Alerts</h3>
                  <button onClick={() => navigate('/alerts')} className="text-xs text-green-600 hover:text-green-700 font-medium">View all</button>
                </div>
                <AlertPanel gardenId={selectedGardenId} compact />
              </div>

              {/* Season Progress - full width */}
              <SeasonProgress frostDates={frostDates} />

              {/* Quick Actions - full width */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Actions</h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setShowJournalForm(true)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-100"
                  >
                    <Eye className="w-4 h-4" />
                    Log Observation
                  </button>
                  <button
                    onClick={() => setShowHarvestForm(true)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-green-50 text-green-700 rounded-lg text-sm font-medium hover:bg-green-100"
                  >
                    <Wheat className="w-4 h-4" />
                    Log Harvest
                  </button>
                  <button
                    onClick={() => navigate('/advisor')}
                    className="flex items-center gap-1.5 px-4 py-2 bg-purple-50 text-purple-700 rounded-lg text-sm font-medium hover:bg-purple-100"
                  >
                    <Bot className="w-4 h-4" />
                    Ask Advisor
                  </button>
                  <button
                    onClick={() => navigate('/calendar')}
                    className="flex items-center gap-1.5 px-4 py-2 bg-amber-50 text-amber-700 rounded-lg text-sm font-medium hover:bg-amber-100"
                  >
                    <Plus className="w-4 h-4" />
                    Add Task
                  </button>
                </div>
              </div>

              {/* Modals */}
              {showJournalForm && (
                <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setShowJournalForm(false)}>
                  <div className="w-full max-w-2xl" onClick={(e) => e.stopPropagation()}>
                    <JournalEntryForm gardenId={selectedGardenId} onClose={() => setShowJournalForm(false)} />
                  </div>
                </div>
              )}
              {showHarvestForm && activePlantings.length > 0 && (
                <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setShowHarvestForm(false)}>
                  <div className="w-full max-w-2xl bg-white rounded-lg p-4" onClick={(e) => e.stopPropagation()}>
                    <HarvestLogger plantingId={activePlantings[0].id} />
                    <button onClick={() => setShowHarvestForm(false)} className="mt-2 text-sm text-gray-500 hover:text-gray-700">Close</button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

const WeatherWidget = ({ current, forecast }: { current: WeatherRecord | null; forecast: WeatherRecord[] }): React.ReactElement => {
  if (!current && forecast.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-gray-400">
          <CloudSun className="w-5 h-5" />
          <span className="text-sm">Sync needed — no recent weather data.</span>
        </div>
      </div>
    );
  }

  const WeatherIcon = current?.frost_risk ? Snowflake : current?.precipitation_mm ? CloudRain : Sun;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-sky-50 rounded-lg border border-blue-100 p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <WeatherIcon className="w-8 h-8 text-blue-500" />
          <div>
            {current?.temp_c !== null && current?.temp_c !== undefined && (
              <p className="text-2xl font-bold text-gray-900">{Math.round(current.temp_c)}°C</p>
            )}
            <div className="flex gap-4 text-xs text-gray-500 mt-1">
              {current?.humidity_pct !== null && current?.humidity_pct !== undefined && (
                <span>Humidity: {current.humidity_pct}%</span>
              )}
              {current?.wind_speed_kmh !== null && current?.wind_speed_kmh !== undefined && (
                <span>Wind: {Math.round(current.wind_speed_kmh)} km/h</span>
              )}
              {current?.frost_risk && <span className="text-red-600 font-medium">Frost Risk!</span>}
            </div>
          </div>
        </div>
        {forecast.length > 0 && (
          <div className="flex gap-3">
            {forecast.slice(0, 3).map((day, i) => (
              <div key={i} className="text-center">
                <p className="text-xs text-gray-500">
                  {new Date(day.timestamp).toLocaleDateString(undefined, { weekday: 'short' })}
                </p>
                <p className="text-sm font-medium text-gray-900 mt-1">
                  {day.temp_c !== null ? `${Math.round(day.temp_c)}°` : '-'}
                </p>
                {day.frost_risk && <Snowflake className="w-3 h-3 text-blue-500 mx-auto mt-0.5" />}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const TodaysTasks = ({
  tasks,
  onComplete,
  isPending,
}: {
  tasks: CalendarEvent[];
  onComplete: (id: number) => void;
  isPending: boolean;
}): React.ReactElement => (
  <div className="bg-white rounded-lg border border-gray-200 p-4">
    <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
      <CheckCircle2 className="w-4 h-4 text-green-500" />
      Today's Tasks
    </h3>
    {tasks.length === 0 ? (
      <p className="text-sm text-gray-400">No tasks today.</p>
    ) : (
      <div className="space-y-2">
        {tasks.map((task) => (
          <div key={task.id} className="flex items-center gap-2">
            <button
              onClick={() => !task.completed && onComplete(task.id)}
              disabled={task.completed || isPending}
              className="flex-shrink-0"
            >
              {task.completed ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : isPending ? (
                <Loader2 className="w-5 h-5 text-gray-300 animate-spin" />
              ) : (
                <Circle className="w-5 h-5 text-gray-300 hover:text-green-400" />
              )}
            </button>
            <span className={`text-sm ${task.completed ? 'text-gray-400 line-through' : 'text-gray-700'}`}>
              {task.title}
            </span>
          </div>
        ))}
      </div>
    )}
  </div>
);

const RecentJournal = ({
  entries,
  onNavigate,
}: {
  entries: JournalEntry[];
  onNavigate: () => void;
}): React.ReactElement => (
  <div className="bg-white rounded-lg border border-gray-200 p-4">
    <div className="flex items-center justify-between mb-3">
      <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <BookOpen className="w-4 h-4 text-blue-500" />
        Recent Journal
      </h3>
      <button onClick={onNavigate} className="text-xs text-green-600 hover:text-green-700 font-medium">
        View all
      </button>
    </div>
    {entries.length === 0 ? (
      <p className="text-sm text-gray-400">No journal entries yet.</p>
    ) : (
      <div className="space-y-2">
        {entries.map((entry) => (
          <div key={entry.id} className="border-l-2 border-green-200 pl-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">{entry.entry_date}</span>
              <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px]">{entry.category}</span>
            </div>
            <p className="text-sm text-gray-700 mt-0.5 line-clamp-2">{entry.content}</p>
          </div>
        ))}
      </div>
    )}
  </div>
);

const SeasonProgress = ({ frostDates }: { frostDates: FrostDatesResult | null }): React.ReactElement => {
  if (!frostDates || !frostDates.last_spring_frost || !frostDates.first_fall_frost) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Growing Season</h3>
        <p className="text-sm text-gray-400">Frost date data not available. Sync weather to calculate.</p>
      </div>
    );
  }

  const today = new Date();
  const springFrost = new Date(frostDates.last_spring_frost + 'T00:00:00');
  const fallFrost = new Date(frostDates.first_fall_frost + 'T00:00:00');
  const totalDays = Math.max(1, (fallFrost.getTime() - springFrost.getTime()) / (1000 * 60 * 60 * 24));
  const elapsed = (today.getTime() - springFrost.getTime()) / (1000 * 60 * 60 * 24);
  const progress = Math.max(0, Math.min(100, (elapsed / totalDays) * 100));
  const isGrowing = elapsed >= 0 && elapsed <= totalDays;
  const daysIntoSeason = Math.max(0, Math.round(elapsed));
  const daysUntilSeason = elapsed < 0 ? Math.abs(Math.round(elapsed)) : 0;
  const daysRemaining = Math.max(0, Math.round(totalDays - elapsed));

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Growing Season</h3>
      <div className="relative h-4 bg-gray-100 rounded-full overflow-hidden mb-2">
        <div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-green-400 to-green-600 rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>Last frost: {frostDates.last_spring_frost}</span>
        <span className="font-medium text-gray-700">
          {isGrowing
            ? `${daysIntoSeason} days in (${daysRemaining} remaining)`
            : daysUntilSeason > 0
              ? `${daysUntilSeason} days until growing season`
              : 'Season complete'}
        </span>
        <span>First frost: {frostDates.first_fall_frost}</span>
      </div>
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

// Keep StatusBadge exported for potential external use
void StatusBadge;

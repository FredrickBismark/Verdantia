import { useState, useCallback } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import type { EventClickArg, DateSelectArg } from '@fullcalendar/core';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, X, CheckCircle, AlertTriangle, Zap } from 'lucide-react';
import { useGardenStore } from '../stores/gardenStore';
import { calendarApi } from '../api/calendar';
import type { CalendarEvent } from '../types';

export const CalendarPage = (): React.ReactElement => {
  const { selectedGardenId } = useGardenStore();
  const queryClient = useQueryClient();

  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newEventDate, setNewEventDate] = useState('');
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventType, setNewEventType] = useState('task');
  const [alertMsg, setAlertMsg] = useState<string | null>(null);

  const { data: eventsData, isLoading } = useQuery({
    queryKey: ['events', selectedGardenId],
    queryFn: () =>
      calendarApi.listEvents(selectedGardenId!, { limit: 200 }),
    enabled: selectedGardenId !== null,
  });

  const completeMutation = useMutation({
    mutationFn: (eventId: number) => calendarApi.completeEvent(eventId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['events'] });
      setSelectedEvent(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (eventId: number) => calendarApi.deleteEvent(eventId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['events'] });
      setSelectedEvent(null);
    },
  });

  const createMutation = useMutation({
    mutationFn: () =>
      calendarApi.createEvent(selectedGardenId!, {
        event_type: newEventType,
        title: newEventTitle,
        scheduled_date: newEventDate,
        source: 'manual',
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['events'] });
      setShowCreateForm(false);
      setNewEventTitle('');
      setNewEventDate('');
    },
  });

  const weatherAlertsMutation = useMutation({
    mutationFn: () => calendarApi.weatherAlerts(selectedGardenId!),
    onSuccess: (res) => {
      void queryClient.invalidateQueries({ queryKey: ['events'] });
      setAlertMsg(`Created ${res.count} weather alert event(s)`);
      setTimeout(() => setAlertMsg(null), 4000);
    },
  });

  const handleEventClick = useCallback((info: EventClickArg): void => {
    const events = eventsData?.data ?? [];
    const event = events.find((e) => String(e.id) === info.event.id);
    setSelectedEvent(event ?? null);
  }, [eventsData]);

  const handleDateSelect = useCallback((info: DateSelectArg): void => {
    setNewEventDate(info.startStr);
    setShowCreateForm(true);
  }, []);

  const fcEvents = (eventsData?.data ?? []).map((e) => ({
    id: String(e.id),
    title: e.title,
    start: e.scheduled_date,
    backgroundColor: e.color ?? undefined,
    borderColor: e.color ?? undefined,
    classNames: e.completed ? ['opacity-50', 'line-through'] : [],
  }));

  if (!selectedGardenId) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Calendar</h1>
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          Select a garden to view its calendar.
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
        <div className="flex gap-2">
          <button
            onClick={() => weatherAlertsMutation.mutate()}
            disabled={weatherAlertsMutation.isPending}
            className="flex items-center gap-2 px-3 py-2 bg-pink-50 border border-pink-200 text-pink-700 rounded-lg hover:bg-pink-100 text-sm"
          >
            <AlertTriangle size={14} />
            Weather Alerts
          </button>
          <button
            onClick={() => { setNewEventDate(''); setShowCreateForm(true); }}
            className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
          >
            <Plus size={14} />
            Add Event
          </button>
        </div>
      </div>

      {alertMsg && (
        <div className="mb-4 px-4 py-2 bg-pink-50 border border-pink-200 text-pink-700 rounded-lg text-sm flex items-center gap-2">
          <Zap size={14} />
          {alertMsg}
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {isLoading ? (
          <div className="text-gray-400 text-sm p-8 text-center">Loading calendar…</div>
        ) : (
          <FullCalendar
            plugins={[dayGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            selectable
            events={fcEvents}
            eventClick={handleEventClick}
            select={handleDateSelect}
            height="auto"
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,dayGridWeek',
            }}
          />
        )}
      </div>

      {/* Event detail panel */}
      {selectedEvent && (
        <div className="fixed inset-y-0 right-0 w-80 bg-white shadow-xl border-l border-gray-200 p-5 overflow-y-auto z-50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 text-sm">Event Detail</h3>
            <button onClick={() => setSelectedEvent(null)}>
              <X size={16} className="text-gray-400 hover:text-gray-600" />
            </button>
          </div>

          <div
            className="w-full h-1 rounded mb-4"
            style={{ backgroundColor: selectedEvent.color ?? '#6b7280' }}
          />

          <dl className="space-y-2 text-sm mb-6">
            <div>
              <dt className="text-xs text-gray-400 uppercase tracking-wide">Title</dt>
              <dd className="font-medium text-gray-900">{selectedEvent.title}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-400 uppercase tracking-wide">Date</dt>
              <dd>{selectedEvent.scheduled_date}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-400 uppercase tracking-wide">Type</dt>
              <dd className="capitalize">{selectedEvent.event_type.replace('_', ' ')}</dd>
            </div>
            {selectedEvent.priority && (
              <div>
                <dt className="text-xs text-gray-400 uppercase tracking-wide">Priority</dt>
                <dd className="capitalize">{selectedEvent.priority}</dd>
              </div>
            )}
            {selectedEvent.description && (
              <div>
                <dt className="text-xs text-gray-400 uppercase tracking-wide">Notes</dt>
                <dd className="text-gray-600">{selectedEvent.description}</dd>
              </div>
            )}
            <div>
              <dt className="text-xs text-gray-400 uppercase tracking-wide">Source</dt>
              <dd className="capitalize">{selectedEvent.source}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-400 uppercase tracking-wide">Status</dt>
              <dd>{selectedEvent.completed ? '✓ Completed' : 'Pending'}</dd>
            </div>
          </dl>

          {!selectedEvent.completed && (
            <button
              onClick={() => completeMutation.mutate(selectedEvent.id)}
              disabled={completeMutation.isPending}
              className="w-full flex items-center justify-center gap-2 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm mb-2"
            >
              <CheckCircle size={14} />
              Mark Complete
            </button>
          )}
          <button
            onClick={() => deleteMutation.mutate(selectedEvent.id)}
            disabled={deleteMutation.isPending}
            className="w-full py-2 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 text-sm"
          >
            Delete Event
          </button>
        </div>
      )}

      {/* Create event form */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">New Event</h3>
              <button onClick={() => setShowCreateForm(false)}>
                <X size={16} className="text-gray-400" />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Title</label>
                <input
                  type="text"
                  value={newEventTitle}
                  onChange={(e) => setNewEventTitle(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="Event title"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Date</label>
                <input
                  type="date"
                  value={newEventDate}
                  onChange={(e) => setNewEventDate(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Type</label>
                <select
                  value={newEventType}
                  onChange={(e) => setNewEventType(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="task">Task</option>
                  <option value="water">Water</option>
                  <option value="fertilize">Fertilize</option>
                  <option value="harvest">Harvest</option>
                  <option value="transplant">Transplant</option>
                  <option value="pest_check">Pest Check</option>
                  <option value="prune">Prune</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2 mt-5">
              <button
                onClick={() => setShowCreateForm(false)}
                className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={() => createMutation.mutate()}
                disabled={!newEventTitle || !newEventDate || createMutation.isPending}
                className="flex-1 py-2 bg-green-600 text-white rounded-lg text-sm disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

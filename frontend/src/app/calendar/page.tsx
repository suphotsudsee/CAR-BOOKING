'use client';

import { useCallback, useMemo, useState } from 'react';
import { addMinutes } from 'date-fns';
import moment from 'moment';
import 'moment/locale/th';
import { Calendar as BigCalendar, momentLocalizer, SlotInfo, View, Views } from 'react-big-calendar';
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore react-big-calendar types do not include the drag and drop addon typings
import withDragAndDrop from 'react-big-calendar/lib/addons/dragAndDrop';
import 'react-big-calendar/lib/addons/dragAndDrop/styles.css';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { CalendarRange, CalendarSearch, RefreshCcw } from 'lucide-react';

import { CalendarEventDialog } from '@/components/calendar/CalendarEventDialog';
import { CalendarExportMenu } from '@/components/calendar/CalendarExportMenu';
import { CalendarFiltersPanel, CalendarFiltersState, ResourceMode } from '@/components/calendar/CalendarFiltersPanel';
import { ConflictContext, ConflictResolutionPanel } from '@/components/calendar/ConflictResolutionPanel';
import {
  CalendarDriverResource,
  CalendarEvent,
  CalendarStatus,
  CalendarVehicleResource,
  calendarDrivers,
  calendarVehicles,
  initialCalendarEvents,
} from '@/components/calendar/sampleData';

moment.locale('th');
const localizer = momentLocalizer(moment);
type CalendarResource =
  | (CalendarVehicleResource & { resourceId: string; resourceTitle: string })
  | (CalendarDriverResource & { resourceId: string; resourceTitle: string });
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const DragAndDropCalendar = withDragAndDrop<CalendarEvent, CalendarResource>(BigCalendar as any);

const thaiDateFormatter = new Intl.DateTimeFormat('th-TH', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

const timeFormatter = new Intl.DateTimeFormat('th-TH', {
  hour: '2-digit',
  minute: '2-digit',
});

type EventRange = {
  start: Date;
  end: Date;
  vehicleId?: string;
  driverId?: string;
};

function hasOverlap(a: CalendarEvent, b: CalendarEvent) {
  return a.start < b.end && b.start < a.end;
}

function sortEvents(events: CalendarEvent[]) {
  return [...events].sort((first, second) => first.start.getTime() - second.start.getTime());
}

function detectConflicts(candidate: CalendarEvent, others: CalendarEvent[]) {
  return others.filter((event) => {
    if (event.id === candidate.id) return false;
    const sameVehicle = event.vehicleId === candidate.vehicleId;
    const sameDriver = event.driverId === candidate.driverId;
    if (!sameVehicle && !sameDriver) return false;
    return hasOverlap(candidate, event);
  });
}

function buildSuggestions(
  pending: CalendarEvent,
  conflicts: CalendarEvent[],
  events: CalendarEvent[],
): ConflictContext['suggestions'] {
  const suggestions: ConflictContext['suggestions'] = [];
  const durationMs = pending.end.getTime() - pending.start.getTime();

  const vehicleConflicts = conflicts.filter((conflict) => conflict.vehicleId === pending.vehicleId);
  if (vehicleConflicts.length > 0) {
    const latestEnd = vehicleConflicts.reduce(
      (latest, conflict) => (conflict.end > latest ? conflict.end : latest),
      vehicleConflicts[0].end,
    );
    const bufferStart = addMinutes(latestEnd, 15);
    const bufferEnd = new Date(bufferStart.getTime() + durationMs);
    const available = !events.some(
      (event) => event.vehicleId === pending.vehicleId && hasOverlap({ ...event, start: bufferStart, end: bufferEnd }, event),
    );
    if (available) {
      suggestions.push({
        id: `${pending.id}-vehicle-delay`,
        label: 'เลื่อนเวลาหลังคิวเดิม',
        description: `ใช้รถคันเดิม เริ่มหลัง ${timeFormatter.format(latestEnd)} พร้อม buffer 15 นาที`,
        start: bufferStart,
        end: bufferEnd,
      });
    }
  }

  const driverConflicts = conflicts.filter((conflict) => conflict.driverId === pending.driverId);
  if (driverConflicts.length > 0) {
    const latestEnd = driverConflicts.reduce(
      (latest, conflict) => (conflict.end > latest ? conflict.end : latest),
      driverConflicts[0].end,
    );
    const bufferStart = addMinutes(latestEnd, 15);
    const bufferEnd = new Date(bufferStart.getTime() + durationMs);
    const available = !events.some(
      (event) => event.driverId === pending.driverId && hasOverlap({ ...event, start: bufferStart, end: bufferEnd }, event),
    );
    if (available) {
      suggestions.push({
        id: `${pending.id}-driver-delay`,
        label: 'ปรับเวลาสำหรับพนักงานขับรถ',
        description: `เริ่มหลังภารกิจก่อนหน้าของคนขับ เวลา ${timeFormatter.format(latestEnd)}`,
        start: bufferStart,
        end: bufferEnd,
      });
    }
  }

  const alternativeVehicle = calendarVehicles.find((vehicle) => {
    if (vehicle.id === pending.vehicleId) return false;
    return !events.some((event) => event.vehicleId === vehicle.id && hasOverlap(pending, event));
  });
  if (alternativeVehicle) {
    suggestions.push({
      id: `${pending.id}-vehicle-alt`,
      label: `ใช้รถสำรอง: ${alternativeVehicle.name}`,
      description: `${alternativeVehicle.type} · ${alternativeVehicle.capacity} ที่นั่ง`,
      vehicleId: alternativeVehicle.id,
    });
  }

  const alternativeDriver = calendarDrivers.find((driver) => {
    if (driver.id === pending.driverId) return false;
    return !events.some((event) => event.driverId === driver.id && hasOverlap(pending, event));
  });
  if (alternativeDriver) {
    suggestions.push({
      id: `${pending.id}-driver-alt`,
      label: `สลับพนักงานขับรถ: ${alternativeDriver.name}`,
      description: `ความถนัด: ${alternativeDriver.skills.slice(0, 3).join(', ')}`,
      driverId: alternativeDriver.id,
    });
  }

  return suggestions;
}

const statusStyles: Record<CalendarStatus, { bg: string; border: string }> = {
  planned: { bg: '#e0f2fe', border: '#0284c7' },
  pending: { bg: '#fef3c7', border: '#f59e0b' },
  confirmed: { bg: '#dcfce7', border: '#22c55e' },
  inProgress: { bg: '#dbeafe', border: '#3b82f6' },
  completed: { bg: '#e2e8f0', border: '#475569' },
  cancelled: { bg: '#fee2e2', border: '#ef4444' },
};

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>(() => sortEvents(initialCalendarEvents));
  const [currentView, setCurrentView] = useState<View>(Views.WEEK);
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [resourceMode, setResourceMode] = useState<ResourceMode>('vehicle');
  const [filters, setFilters] = useState<CalendarFiltersState>({
    statuses: [],
    vehicleTypes: [],
    driverSkills: [],
    resourceIds: [],
    search: '',
    allowSharing: null,
  });
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [dialogRange, setDialogRange] = useState<EventRange | null>(null);
  const [conflictContext, setConflictContext] = useState<ConflictContext | null>(null);
  const [pendingEvent, setPendingEvent] = useState<CalendarEvent | null>(null);

  const resourceList = resourceMode === 'vehicle' ? calendarVehicles : calendarDrivers;

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      if (filters.statuses.length > 0 && !filters.statuses.includes(event.status)) return false;
      if (filters.vehicleTypes.length > 0) {
        const vehicle = calendarVehicles.find((item) => item.id === event.vehicleId);
        if (!vehicle || !filters.vehicleTypes.includes(vehicle.type)) return false;
      }
      if (filters.driverSkills.length > 0) {
        const driver = calendarDrivers.find((item) => item.id === event.driverId);
        if (!driver || !driver.skills.some((skill) => filters.driverSkills.includes(skill))) return false;
      }
      if (filters.resourceIds.length > 0) {
        const resourceId = resourceMode === 'vehicle' ? event.vehicleId : event.driverId;
        if (!filters.resourceIds.includes(resourceId)) return false;
      }
      if (typeof filters.allowSharing === 'boolean') {
        if (Boolean(event.allowSharing) !== filters.allowSharing) return false;
      }
      if (filters.search.trim().length > 0) {
        const haystack = `${event.title} ${event.requester} ${event.department} ${event.location}`.toLowerCase();
        if (!haystack.includes(filters.search.trim().toLowerCase())) return false;
      }
      return true;
    });
  }, [events, filters, resourceMode]);

  const displayedEvents = useMemo(() => {
    return filteredEvents.map((event) => ({
      ...event,
      resourceId: resourceMode === 'vehicle' ? event.vehicleId : event.driverId,
    }));
  }, [filteredEvents, resourceMode]);

  const calendarResources = useMemo<CalendarResource[]>(() => {
    return resourceList.map((resource) => ({
      ...resource,
      resourceId: resource.id,
      resourceTitle: resource.name,
    }));
  }, [resourceList]);

  const handleEventUpdate = useCallback(
    (updated: CalendarEvent) => {
      const others = events.filter((event) => event.id !== updated.id);
      const conflicts = detectConflicts(updated, others);
      if (conflicts.length > 0) {
        setPendingEvent(updated);
        setConflictContext({
          pendingEvent: updated,
          conflicts,
          suggestions: buildSuggestions(updated, conflicts, others),
        });
        return;
      }
      setEvents(sortEvents([...others, updated]));
      setConflictContext(null);
      setPendingEvent(null);
      setEditingEvent(null);
      setDialogRange(null);
      setDialogOpen(false);
    },
    [events],
  );

  const normalizeDate = useCallback((value: Date | string) => (value instanceof Date ? value : new Date(value)), []);

  const handleSelectSlot = useCallback(
    (slot: SlotInfo) => {
      const start = normalizeDate(slot.start as Date | string);
      const end = slot.end ? normalizeDate(slot.end as Date | string) : addMinutes(start, 60);
      const resourceId = typeof slot.resourceId === 'string' ? slot.resourceId : slot.resourceId?.toString();
      setEditingEvent(null);
      setDialogRange({
        start,
        end,
        vehicleId: resourceMode === 'vehicle' ? resourceId ?? calendarVehicles[0]?.id : calendarVehicles[0]?.id,
        driverId: resourceMode === 'driver' ? resourceId ?? calendarDrivers[0]?.id : calendarDrivers[0]?.id,
      });
      setDialogOpen(true);
    },
    [normalizeDate, resourceMode],
  );

  const handleSelectEvent = useCallback(
    (event: CalendarEvent) => {
      const original = events.find((item) => item.id === event.id) ?? event;
      setEditingEvent(original);
      setDialogRange({
        start: original.start,
        end: original.end,
        vehicleId: original.vehicleId,
        driverId: original.driverId,
      });
      setDialogOpen(true);
    },
    [events],
  );

  const handleDialogSave = useCallback(
    (event: CalendarEvent) => {
      handleEventUpdate(event);
    },
    [handleEventUpdate],
  );

  const handleDeleteEvent = useCallback(
    (eventId: string) => {
      setEvents((previous) => previous.filter((event) => event.id !== eventId));
      setDialogOpen(false);
      setEditingEvent(null);
    },
    [],
  );

  const handleEventDrop = useCallback(
    ({
      event,
      start,
      end,
      resourceId,
    }: {
      event: CalendarEvent;
      start: Date | string;
      end: Date | string;
      resourceId?: string | number;
    }) => {
      const original = events.find((item) => item.id === event.id);
      if (!original) return;
      const updated: CalendarEvent = {
        ...original,
        start: normalizeDate(start),
        end: normalizeDate(end),
        vehicleId: resourceMode === 'vehicle' && resourceId ? String(resourceId) : original.vehicleId,
        driverId: resourceMode === 'driver' && resourceId ? String(resourceId) : original.driverId,
      };
      handleEventUpdate(updated);
    },
    [events, handleEventUpdate, normalizeDate, resourceMode],
  );

  const handleEventResize = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: Date | string; end: Date | string }) => {
      const original = events.find((item) => item.id === event.id);
      if (!original) return;
      handleEventUpdate({ ...original, start: normalizeDate(start), end: normalizeDate(end) });
    },
    [events, handleEventUpdate, normalizeDate],
  );

  const handleConflictApply = useCallback(
    (event: CalendarEvent) => {
      handleEventUpdate(event);
      setConflictContext(null);
      setPendingEvent(null);
    },
    [handleEventUpdate],
  );

  const handleConflictKeep = useCallback(() => {
    if (!pendingEvent) return;
    setEvents((previous) => sortEvents([...previous.filter((event) => event.id !== pendingEvent.id), { ...pendingEvent, color: '#fb923c' }]));
    setConflictContext(null);
    setPendingEvent(null);
    setDialogOpen(false);
    setEditingEvent(null);
  }, [pendingEvent]);

  const handleConflictDismiss = useCallback(() => {
    setConflictContext(null);
    setPendingEvent(null);
  }, []);

  const eventStyleGetter = useCallback((event: CalendarEvent) => {
    if (event.color) {
      return {
        style: {
          backgroundColor: event.color,
          borderColor: '#fb923c',
          color: '#fff',
        },
      };
    }
    const palette = statusStyles[event.status];
    return {
      style: {
        backgroundColor: palette.bg,
        borderColor: palette.border,
        color: '#0f172a',
      },
    };
  }, []);

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  const minTime = useMemo(() => {
    const date = new Date(currentDate);
    date.setHours(6, 0, 0, 0);
    return date;
  }, [currentDate]);

  const maxTime = useMemo(() => {
    const date = new Date(currentDate);
    date.setHours(22, 0, 0, 0);
    return date;
  }, [currentDate]);

  return (
    <div className="space-y-6 p-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">ปฏิทินการใช้รถและพนักงานขับรถ</h1>
          <p className="mt-1 text-sm text-gray-600">
            มุมมองรวมของภารกิจทั้งหมด สามารถสลับระหว่างมุมมองรถยนต์และพนักงานขับรถ พร้อมลากวางเพื่อปรับตาราง
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-gray-500">
            <span className="inline-flex items-center gap-1 rounded-full bg-primary-50 px-3 py-1 font-medium text-primary-600">
              <CalendarRange className="h-3.5 w-3.5" /> {thaiDateFormatter.format(currentDate)}
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1 font-medium text-gray-600">
              <CalendarSearch className="h-3.5 w-3.5" /> มุมมอง {resourceMode === 'vehicle' ? 'รถยนต์' : 'พนักงานขับรถ'}
            </span>
            {conflictContext && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 font-medium text-amber-700">
                <RefreshCcw className="h-3.5 w-3.5" /> พบความขัดแย้ง {conflictContext.conflicts.length} รายการ
              </span>
            )}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <CalendarExportMenu events={events} vehicles={calendarVehicles} drivers={calendarDrivers} onPrint={handlePrint} />
          <button
            type="button"
            onClick={() => {
              setEditingEvent(null);
              setDialogRange({
                start: new Date(),
                end: addMinutes(new Date(), 60),
                vehicleId: calendarVehicles[0]?.id,
                driverId: calendarDrivers[0]?.id,
              });
              setDialogOpen(true);
            }}
            className="inline-flex items-center gap-2 rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-700"
          >
            + สร้างภารกิจใหม่
          </button>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[320px,1fr]">
        <CalendarFiltersPanel
          filters={filters}
          onChange={setFilters}
          vehicles={calendarVehicles}
          drivers={calendarDrivers}
          resourceMode={resourceMode}
          onResourceModeChange={setResourceMode}
        />

        <section className="card p-0">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 px-4 py-3">
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="rounded-md border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
                onClick={() => setCurrentDate(new Date())}
              >
                วันนี้
              </button>
              <div className="inline-flex rounded-md border border-gray-200">
                <button
                  type="button"
                  className={`px-3 py-1.5 text-sm font-medium ${currentView === Views.DAY ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-100'}`}
                  onClick={() => setCurrentView(Views.DAY)}
                >
                  วัน
                </button>
                <button
                  type="button"
                  className={`px-3 py-1.5 text-sm font-medium ${currentView === Views.WEEK ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-100'}`}
                  onClick={() => setCurrentView(Views.WEEK)}
                >
                  สัปดาห์
                </button>
                <button
                  type="button"
                  className={`px-3 py-1.5 text-sm font-medium ${currentView === Views.MONTH ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-100'}`}
                  onClick={() => setCurrentView(Views.MONTH)}
                >
                  เดือน
                </button>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="inline-flex items-center gap-1 rounded-full border border-gray-200 px-2 py-1">
                <span className="h-2 w-2 rounded-full bg-[#22c55e]" /> ยืนยันแล้ว
              </span>
              <span className="inline-flex items-center gap-1 rounded-full border border-gray-200 px-2 py-1">
                <span className="h-2 w-2 rounded-full bg-[#f59e0b]" /> รอจัดการ
              </span>
              <span className="inline-flex items-center gap-1 rounded-full border border-gray-200 px-2 py-1">
                <span className="h-2 w-2 rounded-full bg-[#fb923c]" /> รอแก้ไขความขัดแย้ง
              </span>
            </div>
          </div>
          <div className="h-[720px]">
            <DragAndDropCalendar
              localizer={localizer}
              events={displayedEvents}
              resources={calendarResources}
              resourceIdAccessor="resourceId"
              resourceTitleAccessor="resourceTitle"
              startAccessor="start"
              endAccessor="end"
              selectable
              popup
              step={30}
              timeslots={2}
              view={currentView}
              date={currentDate}
              onNavigate={setCurrentDate}
              onView={(next) => setCurrentView(next)}
              onSelectSlot={handleSelectSlot}
              onSelectEvent={handleSelectEvent}
              onEventDrop={handleEventDrop}
              onEventResize={handleEventResize}
              resizable
              eventPropGetter={eventStyleGetter}
              min={minTime}
              max={maxTime}
            />
          </div>
        </section>
      </div>

      {conflictContext && (
        <ConflictResolutionPanel
          context={conflictContext}
          onApply={handleConflictApply}
          onKeep={handleConflictKeep}
          onDismiss={handleConflictDismiss}
          vehicles={calendarVehicles}
          drivers={calendarDrivers}
        />
      )}

      <CalendarEventDialog
        open={isDialogOpen}
        event={editingEvent ?? undefined}
        initialRange={dialogRange ?? undefined}
        onClose={() => {
          setDialogOpen(false);
          setEditingEvent(null);
        }}
        onSave={handleDialogSave}
        onDelete={editingEvent ? handleDeleteEvent : undefined}
        vehicles={calendarVehicles}
        drivers={calendarDrivers}
      />
    </div>
  );
}

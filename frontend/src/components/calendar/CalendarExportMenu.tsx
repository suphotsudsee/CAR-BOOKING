'use client';

import { useMemo, useState } from 'react';
import { Download, FileDown, Printer, Share2, FileType, FileText } from 'lucide-react';

import {
  CalendarDriverResource,
  CalendarEvent,
  CalendarVehicleResource,
} from './sampleData';

interface CalendarExportMenuProps {
  events: CalendarEvent[];
  vehicles: CalendarVehicleResource[];
  drivers: CalendarDriverResource[];
  onPrint?: () => void;
}

interface FileArtifact {
  blob: Blob;
  filename: string;
}

const dateFormatter = new Intl.DateTimeFormat('th-TH', {
  year: 'numeric',
  month: 'short',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});

const dateFormatterShort = new Intl.DateTimeFormat('th-TH', {
  month: 'short',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});

function sanitize(text: string) {
  return text.replace(/[\n\r]+/g, ' ').trim();
}

function toIcsDate(date: Date) {
  return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
}

function escapeIcsText(text: string) {
  return text.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\n/g, '\\n');
}

function createIcs(events: CalendarEvent[], vehicles: CalendarVehicleResource[], drivers: CalendarDriverResource[]): FileArtifact {
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Office Vehicle Booking//Calendar 1.0//TH',
    'CALSCALE:GREGORIAN',
  ];

  for (const event of events) {
    const vehicleName = vehicles.find((vehicle) => vehicle.id === event.vehicleId)?.name ?? event.vehicleId;
    const driverName = drivers.find((driver) => driver.id === event.driverId)?.name ?? event.driverId;
    lines.push('BEGIN:VEVENT');
    lines.push(`UID:${event.id}@office-vehicle-booking`);
    lines.push(`DTSTAMP:${toIcsDate(new Date())}`);
    lines.push(`DTSTART:${toIcsDate(event.start)}`);
    lines.push(`DTEND:${toIcsDate(event.end)}`);
    lines.push(`SUMMARY:${escapeIcsText(event.title)}`);
    lines.push(`DESCRIPTION:${escapeIcsText(`ผู้ขอ: ${event.requester}\\nรถ: ${vehicleName}\\nพนักงานขับรถ: ${driverName}`)}`);
    lines.push(`LOCATION:${escapeIcsText(event.location)}`);
    lines.push(`STATUS:${event.status.toUpperCase()}`);
    lines.push('END:VEVENT');
  }

  lines.push('END:VCALENDAR');
  const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar' });
  return { blob, filename: 'vehicle-booking-calendar.ics' };
}

function createCsv(events: CalendarEvent[], vehicles: CalendarVehicleResource[], drivers: CalendarDriverResource[]): FileArtifact {
  const headers = [
    'Event Title',
    'Requester',
    'Department',
    'Vehicle',
    'Driver',
    'Location',
    'Start',
    'End',
    'Status',
    'Passengers',
    'Sharing',
  ];
  const resolveVehicle = (id: string) => vehicles.find((vehicle) => vehicle.id === id)?.name ?? id;
  const resolveDriver = (id: string) => drivers.find((driver) => driver.id === id)?.name ?? id;

  const rows = events.map((event) => [
    sanitize(event.title),
    sanitize(event.requester),
    sanitize(event.department),
    sanitize(resolveVehicle(event.vehicleId)),
    sanitize(resolveDriver(event.driverId)),
    sanitize(event.location),
    dateFormatter.format(event.start),
    dateFormatter.format(event.end),
    event.status,
    String(event.passengers),
    event.allowSharing ? 'Yes' : 'No',
  ]);

  const csv = [headers, ...rows]
    .map((row) => row.map((value) => `"${value.replace(/"/g, '""')}"`).join(','))
    .join('\n');

  return { blob: new Blob([csv], { type: 'text/csv;charset=utf-8;' }), filename: 'vehicle-booking-calendar.csv' };
}

function escapePdfText(text: string) {
  return text.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');
}

function createPdf(events: CalendarEvent[], vehicles: CalendarVehicleResource[], drivers: CalendarDriverResource[]): FileArtifact {
  const encoder = new TextEncoder();
  const header = '%PDF-1.4\n';
  const objects: string[] = [];
  const offsets: number[] = [];
  let byteLength = encoder.encode(header).length;

  const resolveVehicle = (id: string) => vehicles.find((vehicle) => vehicle.id === id)?.name ?? id;
  const resolveDriver = (id: string) => drivers.find((driver) => driver.id === id)?.name ?? id;

  const lines = events.map((event, index) => {
    const summary = `${dateFormatterShort.format(event.start)} - ${dateFormatterShort.format(event.end)}`;
    const body = `${event.title} | ${resolveVehicle(event.vehicleId)} · ${resolveDriver(event.driverId)}`;
    const location = `สถานที่: ${event.location}`;
    const base = index === 0 ? '' : 'T*\n';
    return `${base}(${escapePdfText(summary)}) Tj\nT*\n(${escapePdfText(body)}) Tj\nT*\n(${escapePdfText(location)}) Tj\nT*`;
  });

  const contentStream = `BT\n/F1 12 Tf\n72 800 Td\n${lines.join('\n')}\nET`;
  const contentBytes = encoder.encode(contentStream).length;

  function pushObject(content: string) {
    const normalized = content.endsWith('\n') ? content : `${content}\n`;
    offsets.push(byteLength);
    objects.push(normalized);
    byteLength += encoder.encode(normalized).length;
  }

  pushObject('1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj');
  pushObject('2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj');
  pushObject('3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj');
  pushObject(`4 0 obj\n<< /Length ${contentBytes} >>\nstream\n${contentStream}\nendstream\nendobj`);
  pushObject('5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj');
  pushObject(`6 0 obj\n<< /Producer (Office Vehicle Booking) /CreationDate (D:${formatPdfDate(new Date())}) >>\nendobj`);

  const body = header + objects.join('');
  const xrefOffset = encoder.encode(body).length;
  let xref = `xref\n0 ${offsets.length + 1}\n`;
  xref += '0000000000 65535 f \n';
  offsets.forEach((offset) => {
    xref += `${offset.toString().padStart(10, '0')} 00000 n \n`;
  });
  xref += `trailer\n<< /Size ${offsets.length + 1} /Root 1 0 R /Info 6 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;

  const pdfContent = body + xref;
  return { blob: new Blob([pdfContent], { type: 'application/pdf' }), filename: 'vehicle-booking-calendar.pdf' };
}

function formatPdfDate(date: Date) {
  const pad = (value: number, length = 2) => value.toString().padStart(length, '0');
  return `${pad(date.getFullYear())}${pad(date.getMonth() + 1)}${pad(date.getDate())}${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`;
}

function downloadFile({ blob, filename }: FileArtifact) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function copyToClipboard(text: string) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
  return Promise.resolve();
}

export function CalendarExportMenu({ events, vehicles, drivers, onPrint }: CalendarExportMenuProps) {
  const [open, setOpen] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const sortedEvents = useMemo(
    () => [...events].sort((a, b) => a.start.getTime() - b.start.getTime()),
    [events],
  );

  const handleShare = async () => {
    const shareUrl = typeof window !== 'undefined' ? window.location.href : '';
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'ตารางงานการใช้รถ',
          text: 'ตรวจสอบตารางงานรถและพนักงานขับรถ',
          url: shareUrl,
        });
        setFeedback('แชร์ลิงก์สำเร็จ');
        setOpen(false);
        return;
      } catch (error) {
        // ถ้าผู้ใช้ยกเลิก ให้ไปคัดลอกลิงก์แทน
      }
    }
    await copyToClipboard(shareUrl);
    setFeedback('คัดลอกลิงก์ไปยังคลิปบอร์ดแล้ว');
    setOpen(false);
  };

  const exportActions = [
    {
      icon: <FileType className="h-4 w-4" />,
      label: 'ส่งออกไฟล์ .ics (ปฏิทิน)',
      action: () => {
        downloadFile(createIcs(sortedEvents, vehicles, drivers));
        setFeedback('บันทึกไฟล์ .ics สำเร็จ');
        setOpen(false);
      },
    },
    {
      icon: <FileText className="h-4 w-4" />,
      label: 'ส่งออกไฟล์ CSV',
      action: () => {
        downloadFile(createCsv(sortedEvents, vehicles, drivers));
        setFeedback('บันทึกไฟล์ CSV สำเร็จ');
        setOpen(false);
      },
    },
    {
      icon: <FileDown className="h-4 w-4" />,
      label: 'สร้างรายงาน PDF',
      action: () => {
        downloadFile(createPdf(sortedEvents, vehicles, drivers));
        setFeedback('สร้างไฟล์ PDF สำเร็จ');
        setOpen(false);
      },
    },
  ];

  const shareActions = [
    {
      icon: <Printer className="h-4 w-4" />,
      label: 'พิมพ์ตารางงาน',
      action: () => {
        if (onPrint) {
          onPrint();
        } else if (typeof window !== 'undefined') {
          window.print();
        }
        setOpen(false);
      },
    },
    {
      icon: <Share2 className="h-4 w-4" />,
      label: 'แชร์หรือคัดลอกลิงก์',
      action: handleShare,
    },
  ];

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="inline-flex items-center gap-2 rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:border-primary-200 hover:bg-primary-50 hover:text-primary-700"
      >
        <Download className="h-4 w-4" /> ส่งออก / แชร์
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-2 w-72 rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
          <p className="px-2 text-xs font-semibold uppercase text-gray-500">การส่งออก</p>
          <div className="mt-2 space-y-1">
            {exportActions.map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={item.action}
                className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm text-gray-700 transition hover:bg-primary-50 hover:text-primary-700"
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </div>
          <p className="mt-3 px-2 text-xs font-semibold uppercase text-gray-500">การแชร์</p>
          <div className="mt-2 space-y-1">
            {shareActions.map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={item.action}
                className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left text-sm text-gray-700 transition hover:bg-primary-50 hover:text-primary-700"
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
      {feedback && (
        <div className="mt-2 text-xs text-gray-500">{feedback}</div>
      )}
    </div>
  );
}

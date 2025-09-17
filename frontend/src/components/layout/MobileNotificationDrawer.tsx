'use client';

import { ReactNode, useEffect, useState } from 'react';

interface MobileNotificationDrawerProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

export function MobileNotificationDrawer({ open, onClose, children }: MobileNotificationDrawerProps) {
  const [dragOffset, setDragOffset] = useState(0);

  useEffect(() => {
    if (!open) {
      setDragOffset(0);
    }
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-slate-900/40 backdrop-blur-sm">
      <div className="flex-1" onClick={onClose} role="presentation" />
      <div
        className="relative rounded-t-3xl bg-white shadow-2xl"
        style={{ transform: `translateY(${dragOffset}px)` }}
        onTouchStart={(event) => {
          setDragOffset(0);
          (event.target as HTMLElement).setAttribute('data-start-y', String(event.touches[0]?.clientY ?? 0));
        }}
        onTouchMove={(event) => {
          const start = Number((event.target as HTMLElement).getAttribute('data-start-y') ?? 0);
          const delta = (event.touches[0]?.clientY ?? start) - start;
          if (delta > 0) {
            setDragOffset(Math.min(delta, 280));
          }
        }}
        onTouchEnd={() => {
          if (dragOffset > 120) {
            onClose();
          }
          setDragOffset(0);
        }}
      >
        <div className="flex flex-col gap-4 px-6 pb-10 pt-5">
          <div className="mx-auto h-1.5 w-16 rounded-full bg-slate-200" />
          {children}
        </div>
      </div>
    </div>
  );
}

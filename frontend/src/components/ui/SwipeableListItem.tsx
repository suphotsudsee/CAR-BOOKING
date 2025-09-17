'use client';

import clsx from 'clsx';
import { ReactNode, useRef, useState } from 'react';

interface SwipeableListItemProps {
  onSwipeLeft?: () => void;
  children: ReactNode;
  actionContent?: ReactNode;
}

const MAX_SWIPE_DISTANCE = 140;
const TRIGGER_DISTANCE = 90;

export function SwipeableListItem({ onSwipeLeft, children, actionContent }: SwipeableListItemProps) {
  const [translateX, setTranslateX] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const startX = useRef(0);
  const animationFrame = useRef<number | null>(null);

  const resetPosition = () => {
    setTranslateX(0);
  };

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    setIsDragging(true);
    startX.current = event.clientX;
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) {
      return;
    }
    const deltaX = event.clientX - startX.current;
    if (deltaX > 0) {
      setTranslateX(0);
      return;
    }

    const nextTranslate = Math.max(deltaX, -MAX_SWIPE_DISTANCE);

    if (animationFrame.current) {
      cancelAnimationFrame(animationFrame.current);
    }

    animationFrame.current = requestAnimationFrame(() => {
      setTranslateX(nextTranslate);
    });
  };

  const handlePointerUp = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) {
      return;
    }
    setIsDragging(false);
    event.currentTarget.releasePointerCapture(event.pointerId);

    if (Math.abs(translateX) >= TRIGGER_DISTANCE) {
      onSwipeLeft?.();
    }
    resetPosition();
  };

  return (
    <div className="relative touch-pan-y select-none">
      <div className="absolute inset-y-0 right-0 flex items-center pr-4 text-sm text-white">
        <div className="rounded-full bg-primary-500 px-4 py-2 shadow-lg">{actionContent}</div>
      </div>
      <div
        role="button"
        tabIndex={0}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onPointerLeave={handlePointerUp}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onSwipeLeft?.();
          }
        }}
        className={clsx(
          'relative z-10 rounded-xl bg-white transition-transform duration-200 will-change-transform',
          isDragging && 'cursor-grabbing'
        )}
        style={{ transform: `translateX(${translateX}px)` }}
      >
        {children}
      </div>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export interface LocationPoint {
  id: string;
  label?: string;
  latitude: number;
  longitude: number;
  accuracy: number | null;
  timestamp: number;
  speed?: number | null;
  heading?: number | null;
  source: 'watch' | 'snapshot';
}

export interface LocationSuggestion {
  id: string;
  targetName: string;
  message: string;
  distance: number;
  type: 'check-in' | 'check-out';
}

export interface AccuracyStatus {
  level: 'excellent' | 'good' | 'poor';
  accuracy: number | null;
  message: string;
}

interface UseLocationTrackingOptions {
  historyLimit?: number;
  accuracyThreshold?: number;
}

const KNOWN_LOCATIONS = [
  {
    id: 'bn-depot',
    name: 'ศูนย์จอดรถบางนา',
    latitude: 13.647512,
    longitude: 100.680388,
    radiusKm: 0.25,
  },
  {
    id: 'hq-checkpoint',
    name: 'สำนักงานใหญ่พระราม 3',
    latitude: 13.696214,
    longitude: 100.530901,
    radiusKm: 0.3,
  },
];

interface CoordinatesLike {
  latitude: number;
  longitude: number;
}

function haversineDistanceKm(a: CoordinatesLike, b: CoordinatesLike): number {
  const toRad = (value: number) => (value * Math.PI) / 180;
  const earthRadiusKm = 6371;

  const dLat = toRad(b.latitude - a.latitude);
  const dLon = toRad(b.longitude - a.longitude);

  const h =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(a.latitude)) * Math.cos(toRad(b.latitude)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));

  return earthRadiusKm * c;
}

export function useLocationTracking(options: UseLocationTrackingOptions = {}) {
  const { historyLimit = 40, accuracyThreshold = 60 } = options;

  const [locationHistory, setLocationHistory] = useState<LocationPoint[]>([]);
  const [currentPosition, setCurrentPosition] = useState<LocationPoint | null>(null);
  const [tracking, setTracking] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [trackingSince, setTrackingSince] = useState<number | null>(null);

  const watchIdRef = useRef<number | null>(null);

  const isSupported = useMemo(() => typeof window !== 'undefined' && 'geolocation' in navigator, []);

  const pushHistory = useCallback(
    (point: LocationPoint) => {
      setLocationHistory((previous) => {
        const next = [point, ...previous];
        if (next.length > historyLimit) {
          return next.slice(0, historyLimit);
        }
        return next;
      });
    },
    [historyLimit],
  );

  const handlePositionUpdate = useCallback(
    (position: GeolocationPosition, source: LocationPoint['source'], label?: string) => {
      const point: LocationPoint = {
        id: `${source}-${position.timestamp}`,
        label,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: typeof position.coords.accuracy === 'number' ? position.coords.accuracy : null,
        timestamp: position.timestamp,
        speed: typeof position.coords.speed === 'number' ? position.coords.speed : null,
        heading: typeof position.coords.heading === 'number' ? position.coords.heading : null,
        source,
      };

      setCurrentPosition(point);
      pushHistory(point);
      setLastError(null);
      return point;
    },
    [pushHistory],
  );

  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null && typeof navigator !== 'undefined' && 'geolocation' in navigator) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setTracking(false);
    setTrackingSince(null);
  }, []);

  useEffect(() => {
    return () => {
      stopTracking();
    };
  }, [stopTracking]);

  const startTracking = useCallback(async () => {
    if (!isSupported) {
      setLastError('อุปกรณ์ไม่รองรับการระบุตำแหน่ง');
      return false;
    }

    if (tracking) {
      return true;
    }

    return new Promise<boolean>((resolve) => {
      const id = navigator.geolocation.watchPosition(
        (position) => {
          handlePositionUpdate(position, 'watch');
          setTracking(true);
          if (!trackingSince) {
            setTrackingSince(Date.now());
          }
          resolve(true);
        },
        (error) => {
          setLastError(error.message);
          stopTracking();
          resolve(false);
        },
        {
          enableHighAccuracy: true,
          maximumAge: 5000,
          timeout: 15000,
        },
      );

      watchIdRef.current = id;
    });
  }, [handlePositionUpdate, isSupported, stopTracking, tracking, trackingSince]);

  const captureSnapshot = useCallback(
    async (label?: string) => {
      if (!isSupported) {
        setLastError('ไม่สามารถระบุตำแหน่งได้ในอุปกรณ์นี้');
        return null;
      }

      return new Promise<LocationPoint | null>((resolve) => {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const point = handlePositionUpdate(position, 'snapshot', label);
            resolve(point);
          },
          (error) => {
            setLastError(error.message);
            resolve(null);
          },
          {
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 12000,
          },
        );
      });
    },
    [handlePositionUpdate, isSupported],
  );

  const totalDistanceKm = useMemo(() => {
    if (locationHistory.length < 2) {
      return 0;
    }

    return locationHistory
      .slice()
      .reverse()
      .reduce((distance, point, index, array) => {
        if (index === 0) return distance;
        const previous = array[index - 1];
        return distance + haversineDistanceKm(previous, point);
      }, 0);
  }, [locationHistory]);

  const suggestions = useMemo<LocationSuggestion[]>(() => {
    if (!currentPosition) {
      return [];
    }

    return KNOWN_LOCATIONS.reduce<LocationSuggestion[]>((list, location) => {
      const distanceKm = haversineDistanceKm(currentPosition, {
        latitude: location.latitude,
        longitude: location.longitude,
        accuracy: null,
        timestamp: Date.now(),
        id: location.id,
        source: 'watch',
      } as LocationPoint);

      const distanceMeters = distanceKm * 1000;
      if (distanceMeters <= location.radiusKm * 1000) {
        list.push({
          id: location.id,
          targetName: location.name,
          message: `คุณอยู่ใกล้${location.name} (${distanceMeters.toFixed(0)} เมตร) ต้องการเช็กอินอัตโนมัติหรือไม่?`,
          distance: distanceMeters,
          type: 'check-in',
        });
      }

      return list;
    }, []);
  }, [currentPosition]);

  const accuracyStatus = useMemo<AccuracyStatus | null>(() => {
    if (!currentPosition) {
      return null;
    }

    const accuracy = currentPosition.accuracy;
    if (accuracy === null || typeof accuracy === 'undefined') {
      return {
        level: 'poor',
        accuracy: null,
        message: 'ไม่สามารถประเมินความแม่นยำของสัญญาณ GPS ได้',
      };
    }

    if (accuracy <= Math.min(20, accuracyThreshold / 2)) {
      return {
        level: 'excellent',
        accuracy,
        message: `ความแม่นยำสูง ~${Math.round(accuracy)} เมตร พร้อมสำหรับการบันทึกข้อมูล`,
      };
    }

    if (accuracy <= accuracyThreshold) {
      return {
        level: 'good',
        accuracy,
        message: `ความแม่นยำปานกลาง ~${Math.round(accuracy)} เมตร โปรดตรวจสอบตำแหน่งก่อนยืนยัน`,
      };
    }

    return {
      level: 'poor',
      accuracy,
      message: `สัญญาณ GPS ไม่เสถียร (~${Math.round(accuracy)} เมตร) กรุณาเคลื่อนย้ายไปยังพื้นที่โล่ง`,
    };
  }, [accuracyThreshold, currentPosition]);

  return {
    isSupported,
    tracking,
    trackingSince,
    currentPosition,
    locationHistory,
    totalDistanceKm,
    suggestions,
    lastError,
    accuracyStatus,
    startTracking,
    stopTracking,
    captureSnapshot,
  } as const;
}

export type UseLocationTrackingReturn = ReturnType<typeof useLocationTracking>;

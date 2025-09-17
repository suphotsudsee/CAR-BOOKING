"use client";

import Image from 'next/image';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Camera, Loader2, MapPin, RefreshCw, ShieldCheck, XCircle } from 'lucide-react';

interface LocationMetadata {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  timestamp: number;
}

export interface CapturedImage {
  dataUrl: string;
  blob: Blob;
  location?: LocationMetadata;
  fileSizeKb: number;
}

interface MobileCameraCaptureProps {
  onCapture?: (image: CapturedImage) => void;
  className?: string;
}

interface CameraError {
  code: string;
  message: string;
}

function toDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result);
      } else {
        reject(new Error('Unable to read image data'));
      }
    };
    reader.onerror = () => reject(new Error('Failed to convert image to data URL'));
    reader.readAsDataURL(blob);
  });
}

async function getLocation(): Promise<LocationMetadata | undefined> {
  if (typeof window === 'undefined' || !('geolocation' in navigator)) {
    return undefined;
  }

  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: typeof position.coords.accuracy === 'number' ? position.coords.accuracy : null,
          timestamp: position.timestamp,
        });
      },
      () => {
        resolve(undefined);
      },
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 5000,
      },
    );
  });
}

export function MobileCameraCapture({ onCapture, className }: MobileCameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isInitialising, setIsInitialising] = useState(true);
  const [isCapturing, setIsCapturing] = useState(false);
  const [cameraError, setCameraError] = useState<CameraError | null>(null);
  const [preview, setPreview] = useState<CapturedImage | null>(null);
  const [locationStatus, setLocationStatus] = useState<'idle' | 'fetching' | 'ready'>('idle');

  const isSupported = useMemo(() => typeof window !== 'undefined' && 'mediaDevices' in navigator, []);

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const initialiseCamera = useCallback(async () => {
    if (!isSupported) {
      setCameraError({ code: 'unsupported', message: 'อุปกรณ์นี้ไม่รองรับการใช้งานกล้องผ่านเบราว์เซอร์' });
      setIsInitialising(false);
      return;
    }

    try {
      setIsInitialising(true);
      setCameraError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'ไม่สามารถเปิดใช้งานกล้องได้';
      setCameraError({ code: 'permission', message });
    } finally {
      setIsInitialising(false);
    }
  }, [isSupported]);

  useEffect(() => {
    initialiseCamera();

    return () => {
      stopStream();
    };
  }, [initialiseCamera, stopStream]);

  const handleCapture = useCallback(async () => {
    if (!videoRef.current) return;

    setIsCapturing(true);
    setLocationStatus('fetching');

    try {
      const video = videoRef.current;
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');

      if (!context) {
        throw new Error('ไม่สามารถสร้างบริบทสำหรับการวาดภาพได้');
      }

      const { videoWidth, videoHeight } = video;
      const maxDimension = 1280;
      const scale = Math.min(1, maxDimension / Math.max(videoWidth, videoHeight));
      canvas.width = Math.round(videoWidth * scale);
      canvas.height = Math.round(videoHeight * scale);
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          (generated) => {
            if (generated) {
              resolve(generated);
            } else {
              reject(new Error('ไม่สามารถบันทึกภาพได้'));
            }
          },
          'image/jpeg',
          0.82,
        );
      });

      const dataUrl = await toDataUrl(blob);
      const location = await getLocation();
      setLocationStatus(location ? 'ready' : 'idle');

      const captured: CapturedImage = {
        dataUrl,
        blob,
        location,
        fileSizeKb: Math.round(blob.size / 1024),
      };

      setPreview(captured);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'เกิดข้อผิดพลาดในการบันทึกภาพ';
      setCameraError({ code: 'capture', message });
    } finally {
      setIsCapturing(false);
    }
  }, []);

  const handleRetake = useCallback(() => {
    setPreview(null);
    setCameraError(null);
    setLocationStatus('idle');
  }, []);

  const handleConfirm = useCallback(() => {
    if (preview && onCapture) {
      onCapture(preview);
    }
    setPreview(null);
    setLocationStatus('idle');
  }, [onCapture, preview]);

  const locationDescription = useMemo(() => {
    if (!preview?.location) {
      if (locationStatus === 'fetching') {
        return 'กำลังดึงข้อมูลตำแหน่ง...';
      }
      return 'ไม่สามารถระบุตำแหน่งได้';
    }

    const { latitude, longitude, accuracy } = preview.location;
    const accuracyText = typeof accuracy === 'number' ? `${Math.round(accuracy)} ม.` : 'ไม่ทราบ';
    return `ละติจูด ${latitude.toFixed(6)}, ลองจิจูด ${longitude.toFixed(6)} (ความแม่นยำ ~${accuracyText})`;
  }, [locationStatus, preview]);

  return (
    <div className={className}>
      <div className="space-y-4 rounded-xl border border-gray-200 bg-white/90 p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-900">ถ่ายภาพสภาพรถ</p>
            <p className="text-xs text-gray-500">
              ระบบจะบีบอัดภาพอัตโนมัติและแนบพิกัดตำแหน่งเพื่อใช้เป็นหลักฐานการเช็กอิน/เช็กเอาต์
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-primary-50 px-2 py-1 text-[11px] font-medium text-primary-600">
            <ShieldCheck className="h-3.5 w-3.5" /> บันทึกปลอดภัย
          </span>
        </div>

        <div className="relative overflow-hidden rounded-xl border border-dashed border-gray-300 bg-gray-50">
          {preview ? (
            <Image
              src={preview.dataUrl}
              alt="ตัวอย่างภาพที่บันทึก"
              width={1280}
              height={720}
              className="h-64 w-full object-cover"
              unoptimized
              priority
            />
          ) : (
            <>
              <video ref={videoRef} playsInline muted className="h-64 w-full object-cover" />
              {isInitialising && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 text-sm text-gray-500">
                  <Loader2 className="mb-2 h-5 w-5 animate-spin" />
                  กำลังเตรียมกล้อง...
                </div>
              )}
            </>
          )}

          {cameraError && !preview && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/90 p-4 text-center text-xs text-rose-600">
              <XCircle className="mb-2 h-5 w-5" />
              <p className="font-medium">{cameraError.message}</p>
              <button
                type="button"
                onClick={initialiseCamera}
                className="mt-2 inline-flex items-center gap-2 rounded-lg border border-rose-200 px-3 py-1.5 text-rose-600 hover:bg-rose-50"
              >
                <RefreshCw className="h-3.5 w-3.5" /> ลองใหม่
              </button>
            </div>
          )}
        </div>

        {preview ? (
          <div className="space-y-3 rounded-lg border border-gray-200 bg-white/70 p-3 text-xs text-gray-600">
            <div className="flex items-center gap-2 font-medium text-gray-700">
              <Camera className="h-4 w-4" /> ภาพถูกบีบอัดเหลือประมาณ {preview.fileSizeKb} KB
            </div>
            <div className="flex items-start gap-2 text-gray-600">
              <MapPin className="mt-0.5 h-4 w-4 flex-shrink-0 text-primary-500" />
              <div>
                <p className="font-medium text-gray-700">ข้อมูลตำแหน่ง</p>
                <p>{locationDescription}</p>
                {preview.location && (
                  <p className="text-[11px] text-gray-400">
                    บันทึกเมื่อ {new Date(preview.location.timestamp).toLocaleString('th-TH')}
                  </p>
                )}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleConfirm}
                className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
              >
                <ShieldCheck className="h-4 w-4" /> ใช้ภาพนี้
              </button>
              <button
                type="button"
                onClick={handleRetake}
                className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
              >
                <RefreshCw className="h-4 w-4" /> ถ่ายใหม่
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleCapture}
              disabled={isInitialising || isCapturing || !!cameraError}
              className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {isCapturing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />} ถ่ายภาพ
            </button>
            <p className="text-[11px] text-gray-500">
              * แนะนำให้หันกล้องไปที่ตัวรถและถือให้มั่นคงเพื่อให้ระบบบันทึกพิกัดได้แม่นยำ
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default MobileCameraCapture;

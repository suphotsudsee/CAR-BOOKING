"use client";
import type { Metadata, Viewport } from 'next';
// @ts-ignore
import './globals.css';
import Providers from './providers';

export const metadata: Metadata = {
  title: 'Office Vehicle Booking System',
  description: 'ระบบจองรถสำนักงาน - Vehicle booking and management system',
  manifest: '/manifest.json',
};

export const viewport: Viewport = {
  themeColor: '#3b82f6',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="th">
      <body>
        <Providers>
          <div id="root">{children}</div>
        </Providers>
      </body>
    </html>
  );
}

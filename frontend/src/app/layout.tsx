Exit code: 0
Wall time: 0.7 seconds
Output:
import type { Metadata, Viewport } from 'next';
import './globals.css';
import Providers from './providers';

export const metadata: Metadata = {
  title: 'Office Vehicle Booking System',
  description: 'เธฃเธฐเธเธเธเธญเธเธฃเธ–เธชเธณเธเธฑเธเธเธฒเธ - Vehicle booking and management system',
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


'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '@/components/auth/AuthLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { USER_ROLES } from '@/context/AuthContext';
import { CheckCircle2, Copy, RefreshCw, ShieldAlert, Smartphone } from 'lucide-react';

type TwoFactorMethod = 'authenticator' | 'sms';

const verificationSchema = z.object({
  code: z
    .string()
    .min(6, 'กรุณากรอกรหัส 6 หลัก')
    .max(6, 'กรุณากรอกรหัส 6 หลัก')
    .regex(/^[0-9]+$/, 'ต้องเป็นตัวเลขเท่านั้น'),
  backupCode: z
    .string()
    .max(10, 'รหัสสำรองต้องไม่เกิน 10 ตัวอักษร')
    .optional(),
});

type VerificationFormValues = z.infer<typeof verificationSchema>;

const methodOptions: { value: TwoFactorMethod; label: string; description: string }[] = [
  {
    value: 'authenticator',
    label: 'แอปพลิเคชัน Authenticator',
    description: 'สแกน QR Code ด้วย Google Authenticator, Microsoft Authenticator หรือแอปที่รองรับ TOTP',
  },
  {
    value: 'sms',
    label: 'SMS OTP',
    description: 'รับรหัส OTP ทางข้อความ SMS สำหรับการเข้าสู่ระบบจากอุปกรณ์ใหม่',
  },
];

function generateBackupCodes() {
  return Array.from({ length: 6 }, () => Math.random().toString(36).slice(2, 7).toUpperCase());
}

function generateSecretKey() {
  return Math.random().toString(36).slice(2, 10).toUpperCase();
}

function AdminTwoFactorContent() {
  const [selectedMethod, setSelectedMethod] = useState<TwoFactorMethod>('authenticator');
  const [secretKey, setSecretKey] = useState(() => generateSecretKey());
  const [backupCodes, setBackupCodes] = useState(() => generateBackupCodes());
  const [verificationMessage, setVerificationMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<VerificationFormValues>({
    resolver: zodResolver(verificationSchema),
    defaultValues: {
      code: '',
      backupCode: '',
    },
  });

  const qrCodeSeed = useMemo(() => `otpauth://totp/CAR-BOOKING:admin?secret=${secretKey}&issuer=CAR-BOOKING`, [secretKey]);

  const handleRefreshSecret = () => {
    setSecretKey(generateSecretKey());
    setBackupCodes(generateBackupCodes());
    setVerificationMessage(null);
    reset({ code: '', backupCode: '' });
  };

  const handleCopy = async (value: string) => {
    try {
      if (typeof navigator === 'undefined' || !navigator.clipboard) {
        throw new Error('Clipboard API not available');
      }
      await navigator.clipboard.writeText(value);
      setVerificationMessage('คัดลอกรหัสไปยังคลิปบอร์ดเรียบร้อยแล้ว');
    } catch (error) {
      setVerificationMessage('ไม่สามารถคัดลอกอัตโนมัติได้ กรุณาคัดลอกด้วยตนเอง');
    }
  };

  const onSubmit = (values: VerificationFormValues) => {
    setVerificationMessage(
      `เปิดใช้งานการยืนยันตัวตนสองชั้นสำเร็จ รหัส ${values.code} จะหมดอายุใน 30 วินาที กรุณาเก็บรักษารหัสสำรองให้ปลอดภัย`,
    );
    reset({ code: '', backupCode: values.backupCode ?? '' });
  };

  return (
    <AuthLayout
      heading="ตั้งค่าการยืนยันตัวตนสองชั้นสำหรับผู้ดูแลระบบ"
      subheading="เพิ่มความปลอดภัยให้กับบัญชีผู้ดูแลด้วยการบังคับใช้ 2FA ทุกครั้งที่เข้าสู่ระบบจากอุปกรณ์ใหม่"
      description="ผู้ดูแลระบบทุกคนจำเป็นต้องเปิดใช้งาน 2FA เพื่อสอดคล้องกับนโยบายความปลอดภัยขององค์กรและมาตรฐาน ISO 27001"
      footer={
        <>
          ต้องการกลับไปยังหน้าจัดการบัญชี?{' '}
          <Link href="/login" className="font-semibold text-primary-600 hover:text-primary-700">
            กลับสู่หน้าเข้าสู่ระบบ
          </Link>
        </>
      }
    >
      <div className="space-y-8">
        <section className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">เลือกวิธีการรับรหัส</h2>
              <p className="mt-1 text-sm text-gray-600">
                ระบบรองรับทั้งการใช้งานผ่านแอปพลิเคชัน Authenticator และการรับรหัส OTP ผ่าน SMS สำหรับสถานการณ์ฉุกเฉิน
              </p>
            </div>
            <button
              type="button"
              onClick={handleRefreshSecret}
              className="inline-flex items-center gap-2 rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              สร้างรหัสใหม่
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {methodOptions.map((method) => (
              <button
                key={method.value}
                type="button"
                onClick={() => setSelectedMethod(method.value)}
                className={`flex h-full flex-col items-start gap-3 rounded-xl border p-5 text-left transition-all ${
                  selectedMethod === method.value
                    ? 'border-primary-500 bg-primary-50 shadow-sm'
                    : 'border-gray-200 bg-white hover:border-primary-300'
                }`}
              >
                <div className="flex items-center gap-3 text-sm font-semibold text-gray-900">
                  {method.value === 'authenticator' ? (
                    <ShieldAlert className="h-5 w-5 text-primary-500" aria-hidden="true" />
                  ) : (
                    <Smartphone className="h-5 w-5 text-primary-500" aria-hidden="true" />
                  )}
                  {method.label}
                </div>
                <p className="text-xs text-gray-600">{method.description}</p>
              </button>
            ))}
          </div>
          <div className="rounded-lg border-l-4 border-primary-400 bg-primary-50/80 p-4 text-sm text-primary-900">
            {selectedMethod === 'authenticator' ? (
              <p>
                เปิดแอป Google Authenticator หรือ Microsoft Authenticator แล้วเพิ่มบัญชีใหม่ด้วยการสแกน QR Code ที่แสดงด้านล่าง
                หรือกรอกรหัสลับด้วยตนเองเพื่อสร้างรหัส 6 หลัก
              </p>
            ) : (
              <p>
                เมื่อเลือก SMS OTP ระบบจะส่งรหัส 6 หลักไปยังหมายเลขโทรศัพท์ที่ลงทะเบียนไว้ หากต้องการปรับปรุงข้อมูล กรุณาติดต่อผู้ดูแลระบบหลักขององค์กร
              </p>
            )}
          </div>
        </section>

        <section className="grid gap-6 rounded-xl border border-gray-200 bg-white p-6 shadow-inner sm:grid-cols-[1.3fr_1fr]">
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-gray-900">สแกน QR Code เพื่อตั้งค่า</h3>
            <p className="text-sm text-gray-600">
              ใช้แอปที่รองรับ TOTP สแกน QR Code หรือป้อนรหัสลับด้วยตนเอง หากเลือกวิธี SMS จะใช้รหัสเดียวกันเป็นตัวตรวจสอบ
            </p>
            <div className="rounded-lg border border-dashed border-primary-300 bg-primary-50/70 p-4 text-center">
              <div className="mx-auto flex h-44 w-44 items-center justify-center rounded-lg border border-primary-200 bg-white">
                <span className="text-xs font-semibold text-primary-500">QR CODE
                  <br />
                  {selectedMethod === 'authenticator' ? 'สำหรับแอป Authenticator' : 'สำหรับการยืนยันทาง SMS'}
                </span>
              </div>
              <p className="mt-3 break-all text-xs text-gray-500">ข้อมูล: {qrCodeSeed}</p>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-gray-50 p-3 text-sm">
              <div>
                <p className="font-semibold text-gray-900">รหัสลับ (Secret Key)</p>
                <p className="font-mono text-xs text-gray-600">{secretKey}</p>
              </div>
              <button
                type="button"
                onClick={() => handleCopy(secretKey)}
                className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-100"
              >
                <Copy className="h-4 w-4" aria-hidden="true" /> คัดลอก
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-base font-semibold text-gray-900">รหัสสำรอง (ใช้ครั้งเดียว)</h3>
            <p className="text-sm text-gray-600">
              เก็บรหัสสำรองไว้ในที่ปลอดภัย เมื่อไม่สามารถเข้าถึงอุปกรณ์หลัก คุณยังสามารถเข้าสู่ระบบได้ด้วยรหัสเหล่านี้
            </p>
            <ul className="grid grid-cols-2 gap-3 font-mono text-sm">
              {backupCodes.map((code) => (
                <li key={code} className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-center">
                  {code}
                </li>
              ))}
            </ul>
            <button
              type="button"
              onClick={() => setBackupCodes(generateBackupCodes())}
              className="inline-flex items-center gap-2 rounded-md border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-100"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              สร้างรหัสสำรองใหม่
            </button>
          </div>
        </section>

        <section>
          <h3 className="text-base font-semibold text-gray-900">ยืนยันรหัสเพื่อเปิดใช้งาน</h3>
          <p className="mt-1 text-sm text-gray-600">
            กรอกรหัส 6 หลักจากแอปหรือ SMS และสามารถบันทึกรหัสสำรองที่ใช้ทดแทนได้ในกรณีฉุกเฉิน
          </p>
          <form className="mt-4 space-y-6" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <label htmlFor="code" className="form-label">
                  รหัสยืนยัน 6 หลัก
                </label>
                <input
                  id="code"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  className="form-input"
                  placeholder="เช่น 123456"
                  {...register('code')}
                />
                {errors.code ? <p className="form-error">{errors.code.message}</p> : null}
              </div>

              <div>
                <label htmlFor="backupCode" className="form-label">
                  รหัสสำรอง (ถ้ามี)
                </label>
                <input
                  id="backupCode"
                  type="text"
                  className="form-input"
                  placeholder="เช่น ABCD1"
                  {...register('backupCode')}
                />
                {errors.backupCode ? <p className="form-error">{errors.backupCode.message}</p> : null}
              </div>
            </div>

            <div className="rounded-lg bg-primary-50 p-4 text-sm text-primary-900">
              <p className="font-semibold">ข้อแนะนำสำหรับผู้ดูแลระบบ</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                <li>ตรวจสอบให้แน่ใจว่าอุปกรณ์สำรองถูกเพิ่มไว้ในระบบจัดการทรัพย์สินขององค์กรแล้ว</li>
                <li>หากเปลี่ยนอุปกรณ์ ควรปิดการใช้งาน 2FA เดิมและตั้งค่าใหม่ทันที</li>
                <li>เก็บรหัสสำรองไว้ในตู้เอกสารหรือ Password Manager ที่องค์กรรับรอง</li>
              </ul>
            </div>

            <button type="submit" className="btn-primary flex items-center justify-center gap-2 py-3 text-base">
              <CheckCircle2 className="h-5 w-5" aria-hidden="true" />
              ยืนยันและเปิดใช้งาน 2FA
            </button>

            {verificationMessage ? (
              <div className="rounded-lg bg-success-50 p-4 text-sm text-success-700">{verificationMessage}</div>
            ) : null}
          </form>
        </section>
      </div>
    </AuthLayout>
  );
}

export default function AdminTwoFactorPage() {
  return (
    <ProtectedRoute roles={[USER_ROLES.FLEET_ADMIN, USER_ROLES.MANAGER]}>
      <AdminTwoFactorContent />
    </ProtectedRoute>
  );
}

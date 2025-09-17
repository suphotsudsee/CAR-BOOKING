'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';

const profileSchema = z.object({
  fullName: z.string().min(1, 'กรุณากรอกชื่อ-นามสกุล'),
  email: z.string().email('รูปแบบอีเมลไม่ถูกต้อง'),
  department: z
    .string()
    .max(100, 'แผนกต้องไม่เกิน 100 ตัวอักษร')
    .optional()
    .transform((value) => value ?? ''),
  twoFactorEnabled: z.boolean(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

function ProfileContent() {
  const { user, updateProfile } = useAuth();
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusVariant, setStatusVariant] = useState<'success' | 'error'>('success');
  const [saving, setSaving] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      fullName: user?.fullName ?? '',
      email: user?.email ?? '',
      department: user?.department ?? '',
      twoFactorEnabled: user?.twoFactorEnabled ?? false,
    },
  });

  useEffect(() => {
    if (!user) {
      return;
    }
    reset({
      fullName: user.fullName,
      email: user.email,
      department: user.department ?? '',
      twoFactorEnabled: user.twoFactorEnabled,
    });
  }, [reset, user]);

  const onSubmit = async (values: ProfileFormValues) => {
    setSaving(true);
    setStatusMessage(null);
    try {
      await updateProfile({
        fullName: values.fullName.trim(),
        email: values.email.trim(),
        department: values.department?.trim() ? values.department.trim() : null,
        twoFactorEnabled: values.twoFactorEnabled,
      });
      setStatusVariant('success');
      setStatusMessage('บันทึกการปรับปรุงโปรไฟล์เรียบร้อยแล้ว');
    } catch (error: unknown) {
      setStatusVariant('error');
      const message = error instanceof Error ? error.message : 'ไม่สามารถบันทึกการเปลี่ยนแปลงได้';
      setStatusMessage(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-10">
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">โปรไฟล์ผู้ใช้งาน</h1>
          <p className="mt-2 text-sm text-gray-500">
            จัดการข้อมูลส่วนตัวของคุณและตรวจสอบสถานะเซสชัน ระบบจะออกจากระบบให้อัตโนมัติเมื่อโทเคนหมดอายุเพื่อความปลอดภัยสูงสุด
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-[2fr_1fr]">
          <div className="space-y-6">
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-gray-900">ข้อมูลส่วนบุคคล</h2>
              <p className="mt-1 text-sm text-gray-500">อัปเดตรายละเอียดของคุณเพื่อให้การประสานงานเป็นไปอย่างราบรื่น</p>

              <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-5">
                <div>
                  <label htmlFor="fullName" className="form-label">
                    ชื่อ-นามสกุล
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    className="form-input"
                    placeholder="เช่น สมชาย ใจดี"
                    {...register('fullName')}
                  />
                  {errors.fullName ? <p className="form-error">{errors.fullName.message}</p> : null}
                </div>

                <div>
                  <label htmlFor="email" className="form-label">
                    อีเมลองค์กร
                  </label>
                  <input
                    id="email"
                    type="email"
                    className="form-input"
                    placeholder="name@company.co.th"
                    {...register('email')}
                  />
                  {errors.email ? <p className="form-error">{errors.email.message}</p> : null}
                </div>

                <div>
                  <label htmlFor="department" className="form-label">
                    แผนก / หน่วยงาน
                  </label>
                  <input
                    id="department"
                    type="text"
                    className="form-input"
                    placeholder="เช่น ฝ่ายธุรการ"
                    {...register('department')}
                  />
                  {errors.department ? <p className="form-error">{errors.department.message}</p> : null}
                </div>

                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <label className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      {...register('twoFactorEnabled')}
                    />
                    <span>
                      <span className="block text-sm font-medium text-gray-900">เปิดใช้งานการยืนยันตัวตนสองขั้นตอน</span>
                      <span className="mt-1 block text-xs text-gray-500">
                        เมื่อเปิดใช้งาน ระบบจะขอรหัสยืนยันเพิ่มเติมระหว่างการเข้าสู่ระบบ เพื่อป้องกันการเข้าถึงโดยไม่ได้รับอนุญาต
                      </span>
                    </span>
                  </label>
                </div>

                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <button
                    type="submit"
                    className="btn-primary px-6 py-2"
                    disabled={saving || !isDirty}
                  >
                    {saving ? 'กำลังบันทึก...' : 'บันทึกการเปลี่ยนแปลง'}
                  </button>
                  {statusMessage ? (
                    <span
                      className={
                        statusVariant === 'success'
                          ? 'text-sm text-success-600'
                          : 'text-sm text-red-600'
                      }
                    >
                      {statusMessage}
                    </span>
                  ) : null}
                </div>
              </form>
            </div>
          </div>

          <aside className="space-y-6">
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900">สรุปบัญชี</h3>
              <dl className="mt-4 space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <dt className="text-gray-500">ชื่อผู้ใช้</dt>
                  <dd className="font-medium text-gray-900">{user?.username}</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-gray-500">บทบาท</dt>
                  <dd className="font-medium text-gray-900">{user?.role}</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-gray-500">สถานะ</dt>
                  <dd className="font-medium text-gray-900">
                    {user?.isActive ? 'ใช้งานอยู่' : 'ถูกระงับการใช้งาน'}
                  </dd>
                </div>
                <div className="flex items-start justify-between gap-3">
                  <dt className="text-gray-500">การยืนยัน 2 ขั้นตอน</dt>
                  <dd className="text-right font-medium text-gray-900">
                    {user?.twoFactorEnabled ? 'เปิดใช้งาน' : 'ปิดอยู่'}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="rounded-xl border border-primary-200 bg-primary-50 p-6 text-sm text-primary-800">
              <h4 className="text-base font-semibold text-primary-700">การจัดการเซสชัน</h4>
              <p className="mt-2">
                โทเคนการเข้าสู่ระบบจะถูกจัดเก็บอย่างปลอดภัยและต่ออายุให้โดยอัตโนมัติก่อนหมดอายุ
                หากระบบไม่สามารถต่ออายุได้ คุณจะถูกออกจากระบบโดยอัตโนมัติเพื่อป้องกันความเสี่ยง
              </p>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}

'use client';

import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useState } from 'react';
import { AuthLayout } from '@/components/auth/AuthLayout';

const loginSchema = z.object({
  email: z.string().min(1, 'กรุณากรอกอีเมล').email('รูปแบบอีเมลไม่ถูกต้อง'),
  password: z.string().min(8, 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร'),
  remember: z.boolean().optional(),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionMessage, setSubmissionMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      remember: true,
    },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setIsSubmitting(true);
    setSubmissionMessage(null);

    await new Promise((resolve) => setTimeout(resolve, 600));

    setSubmissionMessage(
      `สวัสดี ${values.email}! ระบบกำลังตรวจสอบสิทธิ์ของคุณและเชื่อมต่อกับแดชบอร์ดการจองรถ`,
    );
    setIsSubmitting(false);
  };

  return (
    <AuthLayout
      heading="ยินดีต้อนรับกลับสู่ระบบ"
      subheading="จัดการคำขอจองรถ อนุมัติการใช้งาน และติดตามการเดินทางได้ง่ายในที่เดียว"
      description="ระบบรองรับการเข้าสู่ระบบทั้งสำหรับเจ้าหน้าที่ ผู้ขับรถ และผู้ดูแลระบบ เพื่อให้กระบวนการเดินรถลื่นไหลตลอดเส้นทาง"
      footer={
        <>
          ยังไม่มีบัญชีใช่ไหม?{' '}
          <Link href="/register" className="font-semibold text-primary-600 hover:text-primary-700">
            ลงทะเบียนที่นี่
          </Link>
          <div className="mt-2">
            <Link href="/reset-password" className="text-sm text-gray-500 hover:text-gray-700">
              ลืมรหัสผ่าน?
            </Link>
          </div>
        </>
      }
    >
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)} noValidate>
        <div>
          <label htmlFor="email" className="form-label">
            อีเมลองค์กร
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className="form-input"
            placeholder="name@company.co.th"
            {...register('email')}
          />
          {errors.email ? <p className="form-error">{errors.email.message}</p> : null}
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="form-label">
              รหัสผ่าน
            </label>
            <Link href="/reset-password" className="text-sm font-medium text-primary-600 hover:text-primary-700">
              ลืมรหัสผ่าน?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            className="form-input"
            placeholder="กรอกรหัสผ่านของคุณ"
            {...register('password')}
          />
          {errors.password ? <p className="form-error">{errors.password.message}</p> : null}
        </div>

        <div className="flex items-center justify-between">
          <label className="inline-flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              {...register('remember')}
            />
            จดจำการเข้าสู่ระบบในอุปกรณ์นี้
          </label>
          <span className="text-xs text-gray-400">เข้ารหัสด้วยมาตรฐาน OAuth 2.0</span>
        </div>

        <button
          type="submit"
          className="btn-primary flex w-full items-center justify-center gap-2 py-3 text-base"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'กำลังตรวจสอบ...' : 'เข้าสู่ระบบ'}
        </button>

        {submissionMessage ? (
          <div className="rounded-lg bg-success-50 p-4 text-sm text-success-700">{submissionMessage}</div>
        ) : null}
      </form>
    </AuthLayout>
  );
}

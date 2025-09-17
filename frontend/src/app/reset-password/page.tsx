'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '@/components/auth/AuthLayout';

const resetSchema = z.object({
  email: z.string().email('กรุณากรอกอีเมลที่ถูกต้อง'),
  method: z.enum(['email', 'sms']),
});

type ResetFormValues = z.infer<typeof resetSchema>;

export default function ResetPasswordPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetFormValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: {
      email: '',
      method: 'email',
    },
  });

  const selectedMethod = watch('method');

  const onSubmit = async (values: ResetFormValues) => {
    setIsSubmitting(true);
    setSuccessMessage(null);

    await new Promise((resolve) => setTimeout(resolve, 700));

    setSuccessMessage(
      values.method === 'email'
        ? `ลิงก์สำหรับตั้งรหัสผ่านใหม่ถูกส่งไปยัง ${values.email} แล้ว`
        : `รหัสยืนยัน 6 หลักถูกส่งไปยังหมายเลขโทรศัพท์ที่ผูกกับบัญชี ${values.email} แล้ว`,
    );
    setIsSubmitting(false);
  };

  return (
    <AuthLayout
      heading="รีเซ็ตรหัสผ่านอย่างปลอดภัย"
      subheading="เลือกรับลิงก์รีเซ็ตผ่านอีเมลหรือรับรหัส OTP ทางโทรศัพท์ เพื่อให้คุณกลับเข้าสู่ระบบได้อย่างรวดเร็ว"
      description="เพื่อความปลอดภัย ระบบจะบันทึกประวัติการรีเซ็ตรหัสผ่านและแจ้งเตือนผู้ดูแลระบบเมื่อเกิดเหตุการณ์ผิดปกติ"
      footer={
        <>
          จำรหัสผ่านได้แล้วใช่ไหม?{' '}
          <Link href="/login" className="font-semibold text-primary-600 hover:text-primary-700">
            กลับไปเข้าสู่ระบบ
          </Link>
        </>
      }
    >
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)} noValidate>
        <div>
          <label htmlFor="email" className="form-label">
            อีเมลที่ใช้สมัคร
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
          <span className="form-label">เลือกรูปแบบการยืนยันตัวตน</span>
          <div className="grid gap-4 sm:grid-cols-2">
            {(
              [
                { value: 'email', label: 'อีเมล', description: 'ส่งลิงก์รีเซ็ตไปยังกล่องจดหมายองค์กรของคุณ' },
                { value: 'sms', label: 'SMS OTP', description: 'รับรหัสยืนยัน 6 หลักผ่านหมายเลขโทรศัพท์ที่ผูกกับบัญชี' },
              ] as const
            ).map((method) => (
              <label
                key={method.value}
                className={`flex cursor-pointer flex-col gap-2 rounded-lg border p-4 transition-all ${
                  selectedMethod === method.value
                    ? 'border-primary-500 bg-primary-50 shadow-sm'
                    : 'border-gray-200 bg-white hover:border-primary-300'
                }`}
              >
                <input
                  type="radio"
                  value={method.value}
                  className="sr-only"
                  {...register('method')}
                />
                <span className="text-sm font-semibold text-gray-900">{method.label}</span>
                <span className="text-xs text-gray-500">{method.description}</span>
              </label>
            ))}
          </div>
          {errors.method ? <p className="form-error">{errors.method.message}</p> : null}
        </div>

        <div className="rounded-lg bg-secondary-50 p-4 text-sm text-secondary-900">
          <p className="font-semibold">คำแนะนำ</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>สำหรับบทบาทผู้ดูแลระบบ จะต้องยืนยันรหัส OTP ก่อนจึงจะตั้งรหัสผ่านใหม่ได้</li>
            <li>หากไม่ได้รับอีเมลภายใน 5 นาที กรุณาตรวจสอบในโฟลเดอร์ Junk หรือ Spam</li>
            <li>การรีเซ็ตรหัสผ่านมากกว่า 3 ครั้งใน 24 ชั่วโมงจะถูกแจ้งเตือนผู้ดูแลระบบอัตโนมัติ</li>
          </ul>
        </div>

        <button
          type="submit"
          className="btn-primary flex w-full items-center justify-center gap-2 py-3 text-base"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'กำลังส่งลิงก์รีเซ็ต...' : 'ส่งคำขอรีเซ็ตรหัสผ่าน'}
        </button>

        {successMessage ? (
          <div className="rounded-lg bg-success-50 p-4 text-sm text-success-700">{successMessage}</div>
        ) : null}
      </form>
    </AuthLayout>
  );
}

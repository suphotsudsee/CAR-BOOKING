'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AuthLayout } from '@/components/auth/AuthLayout';
import { useAuth } from '@/context/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

const registrationSchema = z
  .object({
    fullName: z.string().min(3, 'กรุณากรอกชื่อ-นามสกุล'),
    email: z.string().email('รูปแบบอีเมลไม่ถูกต้อง'),
    password: z
      .string()
      .min(8, 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร')
      .regex(/^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$/, 'ต้องมีตัวใหญ่ ตัวเล็ก และตัวเลขอย่างน้อยอย่างละ 1 ตัว'),
    confirmPassword: z.string(),
    role: z.enum(['employee', 'driver', 'admin'], { required_error: 'กรุณาเลือกบทบาทการใช้งาน' }),
    acceptPolicies: z
      .boolean()
      .refine((value) => value, {
        message: 'กรุณายืนยันว่าคุณได้อ่านและยอมรับนโยบายการใช้งาน',
      }),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'รหัสผ่านยืนยันไม่ตรงกัน',
    path: ['confirmPassword'],
  });

type RegistrationFormValues = z.infer<typeof registrationSchema>;

type ApiUserRole = 'requester' | 'driver' | 'fleet_admin';

const roleDescriptions: Record<RegistrationFormValues['role'], string> = {
  employee: 'ขอจองรถ ติดตามสถานะ และจัดการการเดินทางของทีมได้สะดวก',
  driver: 'รับมอบหมายงานขับรถ ดูตารางเดินรถ และรายงานสถานะได้ทันที',
  admin: 'กำหนดสิทธิ์ผู้ใช้งาน จัดการรถ และตรวจสอบรายงานทั้งหมดในระบบ',
};

const roleMap: Record<RegistrationFormValues['role'], ApiUserRole> = {
  employee: 'requester',
  driver: 'driver',
  admin: 'fleet_admin',
};

function deriveUsername(fullName: string, email: string): string {
  const [localPart] = email.split('@');
  const emailCandidate = (localPart ?? '').replace(/[^a-zA-Z0-9._-]/g, '');
  const nameCandidate = fullName
    .toLowerCase()
    .replace(/\s+/g, '.')
    .replace(/[^a-z0-9._-]/g, '');

  let candidate = emailCandidate || nameCandidate || `user${Date.now()}`;
  candidate = candidate.slice(0, 50);

  if (candidate.length < 3) {
    candidate = candidate.padEnd(3, '0');
  }

  return candidate;
}

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionMessage, setSubmissionMessage] = useState<string | null>(null);
  const [messageVariant, setMessageVariant] = useState<'success' | 'error'>('success');

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegistrationFormValues>({
    resolver: zodResolver(registrationSchema),
    defaultValues: {
      fullName: '',
      email: '',
      password: '',
      confirmPassword: '',
      role: 'employee',
      acceptPolicies: false,
    },
  });

  const selectedRole = watch('role');

  const onSubmit = async (values: RegistrationFormValues) => {
    setIsSubmitting(true);
    setSubmissionMessage(null);

    const username = deriveUsername(values.fullName, values.email);
    const role = roleMap[values.role];

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          email: values.email,
          full_name: values.fullName,
          password: values.password,
          role,
          department: null,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const message = typeof data?.detail === 'string' ? data.detail : 'ไม่สามารถสร้างบัญชีได้';
        throw new Error(message);
      }

      await login({ username, password: values.password, remember: true });

      setMessageVariant('success');
      setSubmissionMessage('สร้างบัญชีสำเร็จ กำลังพาคุณไปยังหน้าโปรไฟล์');
      router.push('/profile');
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'ไม่สามารถสร้างบัญชีได้';
      setMessageVariant('error');
      setSubmissionMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      heading="สร้างบัญชีผู้ใช้งานใหม่"
      subheading="ขับเคลื่อนการจัดการรถขององค์กรด้วยระบบที่ปลอดภัยและออกแบบมาสำหรับการทำงานร่วมกัน"
      description="การลงทะเบียนรองรับทั้งพนักงานทั่วไป คนขับรถ และผู้ดูแลระบบ เพื่อให้การมอบหมายงานและการอนุมัติเป็นเรื่องง่ายตั้งแต่วันแรก"
      footer={
        <>
          มีบัญชีอยู่แล้วใช่ไหม?{' '}
          <Link href="/login" className="font-semibold text-primary-600 hover:text-primary-700">
            เข้าสู่ระบบ
          </Link>
        </>
      }
    >
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)} noValidate>
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <label htmlFor="fullName" className="form-label">
              ชื่อ-นามสกุล
            </label>
            <input
              id="fullName"
              type="text"
              className="form-input"
              placeholder="กรุณากรอกชื่อ-นามสกุล"
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
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <label htmlFor="password" className="form-label">
              รหัสผ่าน
            </label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder="อย่างน้อย 8 ตัวอักษร"
              {...register('password')}
            />
            {errors.password ? <p className="form-error">{errors.password.message}</p> : null}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="form-label">
              ยืนยันรหัสผ่าน
            </label>
            <input
              id="confirmPassword"
              type="password"
              className="form-input"
              placeholder="พิมพ์รหัสผ่านอีกครั้ง"
              {...register('confirmPassword')}
            />
            {errors.confirmPassword ? <p className="form-error">{errors.confirmPassword.message}</p> : null}
          </div>
        </div>

        <div>
          <span className="form-label">เลือกบทบาทในการใช้งาน</span>
          <div className="grid gap-4 sm:grid-cols-3">
            {(
              [
                { value: 'employee', label: 'พนักงาน' },
                { value: 'driver', label: 'คนขับรถ' },
                { value: 'admin', label: 'ผู้ดูแลระบบ' },
              ] as const
            ).map((role) => (
              <label
                key={role.value}
                className={`flex cursor-pointer flex-col gap-2 rounded-lg border p-4 transition-all ${
                  selectedRole === role.value
                    ? 'border-primary-500 bg-primary-50 shadow-sm'
                    : 'border-gray-200 bg-white hover:border-primary-300'
                }`}
              >
                <input
                  type="radio"
                  value={role.value}
                  className="sr-only"
                  {...register('role')}
                />
                <span className="text-sm font-semibold text-gray-900">{role.label}</span>
                <span className="text-xs text-gray-500">{roleDescriptions[role.value]}</span>
              </label>
            ))}
          </div>
          {errors.role ? <p className="form-error">{errors.role.message}</p> : null}
        </div>

        <div className="rounded-lg bg-gray-50 p-4 text-sm text-gray-600">
          <p className="font-medium text-gray-900">ข้อกำหนดด้านความปลอดภัย</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>ตั้งรหัสผ่านอย่างน้อย 8 ตัวอักษร และประกอบด้วยตัวเลข ตัวพิมพ์ใหญ่ และตัวพิมพ์เล็ก</li>
            <li>ผู้ใช้งานบทบาทผู้ดูแลระบบต้องเปิดใช้งานการยืนยันตัวตนสองชั้น (2FA)</li>
            <li>บัญชีจะพร้อมใช้งานได้ทันทีหลังจากลงทะเบียนสำเร็จ ไม่ต้องยืนยันอีเมล</li>
          </ul>
        </div>

        <label className="flex items-start gap-3 text-sm text-gray-600">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            {...register('acceptPolicies')}
          />
          <span>
            ข้าพเจ้ายอมรับ{' '}
            <Link href="#" className="font-medium text-primary-600 hover:text-primary-700">
              เงื่อนไขการใช้งานและนโยบายความเป็นส่วนตัวของระบบการจองรถ
            </Link>
          </span>
        </label>
        {errors.acceptPolicies ? <p className="form-error">{errors.acceptPolicies.message}</p> : null}

        <button
          type="submit"
          className="btn-primary flex w-full items-center justify-center gap-2 py-3 text-base"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'กำลังสร้างบัญชี...' : 'ลงทะเบียน'}
        </button>

        {submissionMessage ? (
          <div
            className={
              messageVariant === 'success'
                ? 'rounded-lg bg-success-50 p-4 text-sm text-success-700'
                : 'rounded-lg bg-red-50 p-4 text-sm text-red-700'
            }
          >
            {submissionMessage}
          </div>
        ) : null}
      </form>
    </AuthLayout>
  );
}

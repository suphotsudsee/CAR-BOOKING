export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            ระบบจองรถสำนักงาน
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Office Vehicle Booking System
          </p>
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              ยินดีต้อนรับ
            </h2>
            <p className="text-gray-600 mb-6">
              ระบบจัดการการจองรถสำนักงานที่ครบครันและใช้งานง่าย
            </p>
            <div className="space-y-3">
              <button className="btn-primary w-full py-3">
                เข้าสู่ระบบ
              </button>
              <button className="btn-secondary w-full py-3">
                ดูคู่มือการใช้งาน
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
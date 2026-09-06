import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="text-2xl font-semibold tracking-tight text-foreground">
            CalorieQ
          </span>
        </div>
        <Outlet />
      </div>
    </div>
  )
}

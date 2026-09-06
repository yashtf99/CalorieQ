import { useQuery } from '@tanstack/react-query'
import { USER_TZ } from '@/lib/tz'
import type { DailySummaryOut, MicrosReportOut, WeeklyReportOut } from '@/types/reports'
import { apiClient } from './client'

export function useDailySummary(date: string) {
  return useQuery({
    queryKey: ['daily-summary', date, USER_TZ],
    queryFn: () =>
      apiClient
        .get<DailySummaryOut>('/reports/daily_summary', { params: { date, tz: USER_TZ } })
        .then((r) => r.data),
  })
}

export function useWeeklyReport(weekOf: string) {
  return useQuery({
    queryKey: ['weekly-report', weekOf, USER_TZ],
    queryFn: () =>
      apiClient
        .get<WeeklyReportOut>('/reports/weekly', { params: { week_of: weekOf, tz: USER_TZ } })
        .then((r) => r.data),
  })
}

export function useWeeklyReportRange(start: string, end: string) {
  return useQuery({
    queryKey: ['weekly-report-range', start, end, USER_TZ],
    queryFn: () =>
      apiClient
        .get<WeeklyReportOut>('/reports/weekly', { params: { start, end, tz: USER_TZ } })
        .then((r) => r.data),
    enabled: !!start && !!end,
  })
}

export function useMicrosReport(start: string, end: string) {
  return useQuery({
    queryKey: ['micros-report', start, end, USER_TZ],
    queryFn: () =>
      apiClient
        .get<MicrosReportOut>('/reports/micros', { params: { start, end, tz: USER_TZ } })
        .then((r) => r.data),
    enabled: !!start && !!end,
  })
}

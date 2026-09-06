import { format } from 'date-fns'
import { create } from 'zustand'

interface DateState {
  selectedDate: string // YYYY-MM-DD
  setDate: (date: string) => void
  goToPrev: () => void
  goToNext: () => void
}

function offsetDate(dateStr: string, days: number): string {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return format(d, 'yyyy-MM-dd')
}

export const useDateStore = create<DateState>()((set) => ({
  selectedDate: format(new Date(), 'yyyy-MM-dd'),
  setDate: (date) => set({ selectedDate: date }),
  goToPrev: () => set((s) => ({ selectedDate: offsetDate(s.selectedDate, -1) })),
  goToNext: () => set((s) => ({ selectedDate: offsetDate(s.selectedDate, 1) })),
}))

import { Trash2 } from 'lucide-react'
import type { MealLogOut } from '@/types/meals'
import { useDeleteMeal } from '@/api/meals'

interface Props {
  entry: MealLogOut
  date: string
}

export default function MealEntryRow({ entry, date }: Props) {
  const deleteMeal = useDeleteMeal(date)

  const handleDelete = () => {
    deleteMeal.mutate(entry.id)
  }

  return (
    <div className="group flex items-center justify-between py-2 px-3 rounded hover:bg-muted/50 transition-colors">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{entry.food_name_snapshot}</p>
        <div className="flex gap-4 text-xs text-muted-foreground">
          <span>{entry.quantity_g.toLocaleString()}g</span>
          <span className="flex gap-1">
            <span>{Math.round(entry.protein_g ?? 0)}P</span>
            <span>{Math.round(entry.carb_g ?? 0)}C</span>
            <span>{Math.round(entry.fat_g ?? 0)}F</span>
          </span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium tabular-nums">
          {Math.round(entry.energy_kcal ?? 0)} kcal
        </span>
        <button
          onClick={handleDelete}
          disabled={deleteMeal.isPending}
          className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive disabled:opacity-50"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

import { useState } from 'react'
import type { MealType, MealLogOut } from '@/types/meals'
import { useMealHistory } from '@/api/meals'
import MealTypeRow from './MealTypeRow'
import AddMealDrawer from './AddMealDrawer'
import EmptyState from '@/components/common/EmptyState'

interface Props {
  date: string
}

export default function MealsSection({ date }: Props) {
  const { data: meals, isLoading } = useMealHistory(date)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [initialMealType, setInitialMealType] = useState<MealType | null>(null)

  const grouped: Record<MealType, MealLogOut[]> = {
    breakfast: [],
    lunch: [],
    snacks: [],
    dinner: [],
  }

  if (meals) {
    for (const meal of meals) {
      grouped[meal.meal_type].push(meal)
    }
  }

  const handleAddMeal = (type: MealType) => {
    setInitialMealType(type)
    setIsDrawerOpen(true)
  }

  const totalMeals = Object.values(grouped).reduce((sum, meals) => sum + meals.length, 0)

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-xl">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="border-b border-border last:border-0 h-12 bg-muted animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <>
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold">Meals</h3>
          <button
            onClick={() => {
              setInitialMealType(null)
              setIsDrawerOpen(true)
            }}
            className="text-xs px-2 py-1 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Add meal
          </button>
        </div>

        <div>
          {(Object.keys(grouped) as MealType[]).map((type) => (
              <MealTypeRow
                key={type}
                type={type}
                entries={grouped[type]}
                date={date}
                onAdd={handleAddMeal}
              />
            ))}
        </div>
      </div>

      <AddMealDrawer
        open={isDrawerOpen}
        onOpenChange={setIsDrawerOpen}
        initialMealType={initialMealType}
        date={date}
      />
    </>
  )
}

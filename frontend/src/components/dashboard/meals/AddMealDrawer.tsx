import { X, Upload, Loader2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { parseISO } from 'date-fns'
import type { MealType } from '@/types/meals'
import type { FoodItemSearchOut } from '@/types/food'
import { scaleMacros } from '@/types/food'
import { useFoodSearchInfinite, useFoodCategories, useRecentFoods } from '@/api/food'
import { useAddMeal } from '@/api/meals'
import { useExtractImage, type ImageExtractionResult } from '@/api/ai'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialMealType: MealType | null
  date: string
}

type View = 'search' | 'detail' | 'custom' | 'image' | 'image-detail'

function QuantitySelector({
  portions,
  quantity,
  portionId,
  multiplier,
  onQuantityChange,
  onPortionChange,
  onMultiplierChange,
}: {
  portions: Array<{ id: string; description: string; gram_weight: number }>
  quantity: number
  portionId?: string
  multiplier?: number
  onQuantityChange: (q: number) => void
  onPortionChange: (id: string) => void
  onMultiplierChange: (m: number) => void
}) {
  const isUnitPortion = (desc: string) => /^\d+(\.\d+)?\s*(g|ml|oz)$/i.test(desc)
  const hasNonGramPortion = portions.some((p) => isUnitPortion(p.description) && p.gram_weight !== 1)

  if (portions.length > 0 && hasNonGramPortion) {
    const gramPortion = portions.find((p) => p.gram_weight === 1)
    const unitPortions = portions.filter((p) => isUnitPortion(p.description))

    return (
      <div className="space-y-3">
        <div className="flex gap-2 flex-wrap">
          {unitPortions.map((p) => (
            <button
              key={p.id}
              onClick={() => onPortionChange(p.id)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                portionId === p.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              {p.description}
            </button>
          ))}
          {gramPortion && (
            <button
              onClick={() => onPortionChange('')}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                !portionId ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              Custom (g)
            </button>
          )}
        </div>

        {portionId && multiplier !== undefined && (
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="0.1"
              step="0.1"
              value={multiplier}
              onChange={(e) => onMultiplierChange(parseFloat(e.target.value) || 1)}
              className="w-16 px-2 py-1 border border-border rounded text-sm"
            />
            <span className="text-sm text-muted-foreground">×</span>
            <span className="text-sm">
              {(
                (portions.find((p) => p.id === portionId)?.gram_weight ?? 1) * multiplier
              ).toLocaleString()}g
            </span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      <label className="block text-sm font-medium mb-2">Quantity (g)</label>
      <input
        type="number"
        min="1"
        value={quantity}
        onChange={(e) => onQuantityChange(parseFloat(e.target.value) || 0)}
        className="w-full px-3 py-2 border border-border rounded"
      />
    </div>
  )
}

export default function AddMealDrawer({ open, onOpenChange, initialMealType, date }: Props) {
  const [view, setView] = useState<View>('search')
  const [mealType, setMealType] = useState<MealType>(initialMealType ?? 'lunch')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQ, setDebouncedQ] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>()
  const [selectedFood, setSelectedFood] = useState<FoodItemSearchOut | null>(null)
  const [quantity, setQuantity] = useState(100)
  const [portionId, setPortionId] = useState<string>()
  const [multiplier, setMultiplier] = useState(1)
  const [imageData, setImageData] = useState<ImageExtractionResult | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [customFood, setCustomFood] = useState({
    name: '',
    quantity_g: 100,
    energy_kcal: 0,
    protein_g: 0,
    carb_g: 0,
    fat_g: 0,
  })

  const debounceTimeout = useRef<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setMealType(initialMealType ?? 'lunch')
    // Reset to search view when opening or when meal type changes
    setView('search')
    setSearchQuery('')
    setSelectedFood(null)
    setActiveCategory(undefined)
    setImageData(null)
    setImagePreview(null)
  }, [initialMealType, open])

  useEffect(() => {
    if (debounceTimeout.current) clearTimeout(debounceTimeout.current)
    debounceTimeout.current = setTimeout(() => {
      setDebouncedQ(searchQuery)
    }, 300)
    return () => {
      if (debounceTimeout.current) clearTimeout(debounceTimeout.current)
    }
  }, [searchQuery])

  const searchResults = useFoodSearchInfinite(debouncedQ, activeCategory, view === 'search' && debouncedQ.length > 0)
  const categories = useFoodCategories(debouncedQ, view === 'search' && debouncedQ.length > 0)
  const recentFoods = useRecentFoods(5)
  const addMeal = useAddMeal(date)
  const extractImage = useExtractImage()

  const sentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && searchResults.hasNextPage) {
        searchResults.fetchNextPage()
      }
    })

    if (sentinelRef.current) {
      observer.observe(sentinelRef.current)
    }

    return () => observer.disconnect()
  }, [searchResults])

  // Calculate logged_at based on meal type and date
  const getMealDefaultLoggedAt = (mealType: MealType, dateStr: string): string => {
    const MEAL_DEFAULT_HOURS: Record<MealType, number> = {
      breakfast: 9,
      lunch: 13,
      snacks: 17,
      dinner: 21,
    }

    const hour = MEAL_DEFAULT_HOURS[mealType]
    const date = parseISO(dateStr)

    // Create the datetime with the meal's default hour, in the user's timezone
    const loggedAt = new Date(date)
    loggedAt.setHours(hour, 0, 0, 0)

    // Convert to ISO string (will include timezone offset)
    return loggedAt.toISOString()
  }

  const handleAddLinkedMeal = async () => {
    if (!selectedFood) return
    const qty = portionId && selectedFood.portions
      ? (selectedFood.portions.find((p) => p.id === portionId)?.gram_weight ?? 1) * multiplier
      : quantity

    await addMeal.mutateAsync({
      food_item_id: selectedFood.id,
      meal_type: mealType,
      quantity_g: qty,
      logged_at: getMealDefaultLoggedAt(mealType, date),
    })
    onOpenChange(false)
  }

  const handleAddCustomMeal = async () => {
    await addMeal.mutateAsync({
      food_name_snapshot: customFood.name,
      meal_type: mealType,
      quantity_g: customFood.quantity_g,
      energy_kcal: customFood.energy_kcal,
      protein_g: customFood.protein_g,
      carb_g: customFood.carb_g,
      fat_g: customFood.fat_g,
      source: 'user',
      logged_at: getMealDefaultLoggedAt(mealType, date),
    })
    onOpenChange(false)
  }

  const handleAutoFillMacros = () => {
    const kcal = customFood.energy_kcal
    setCustomFood((prev) => ({
      ...prev,
      protein_g: kcal * 0.25 / 4,
      carb_g: kcal * 0.45 / 4,
      fat_g: kcal * 0.30 / 9,
    }))
  }

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Create preview
    const reader = new FileReader()
    reader.onload = (event) => {
      setImagePreview(event.target?.result as string)
    }
    reader.readAsDataURL(file)

    // Extract nutrition
    await extractImage.mutateAsync(file, {
      onSuccess: (data) => {
        setImageData(data)
        setView('image-detail')
        // Pre-fill quantity if available
        if (data.quantity_g) {
          setQuantity(data.quantity_g)
        }
      },
    })
  }

  const handleImageConfirm = async () => {
    if (!imageData) return
    await addMeal.mutateAsync({
      food_name_snapshot: imageData.food_item_name || 'From Image',
      meal_type: mealType,
      quantity_g: quantity,
      energy_kcal: imageData.energy_kcal || 0,
      protein_g: imageData.protein_g,
      carb_g: imageData.carb_g,
      fat_g: imageData.fat_g,
      ...(imageData.fibre_g !== undefined && { fibre_g: imageData.fibre_g }),
      ...(imageData.sodium_mg !== undefined && { sodium_mg: imageData.sodium_mg }),
      source: 'ai',
      logged_at: getMealDefaultLoggedAt(mealType, date),
    })
    onOpenChange(false)
  }

  const scaleImageDataByQuantity = (baseData: ImageExtractionResult, quantityGrams: number) => {
    if (!baseData.quantity_g) return baseData
    const scale = quantityGrams / baseData.quantity_g
    return {
      ...baseData,
      quantity_g: quantityGrams,
      energy_kcal: baseData.energy_kcal ? Math.round(baseData.energy_kcal * scale * 10) / 10 : undefined,
      protein_g: baseData.protein_g ? Math.round(baseData.protein_g * scale * 10) / 10 : undefined,
      carb_g: baseData.carb_g ? Math.round(baseData.carb_g * scale * 10) / 10 : undefined,
      fat_g: baseData.fat_g ? Math.round(baseData.fat_g * scale * 10) / 10 : undefined,
      fibre_g: baseData.fibre_g ? Math.round(baseData.fibre_g * scale * 10) / 10 : undefined,
      sodium_mg: baseData.sodium_mg ? Math.round(baseData.sodium_mg * scale * 10) / 10 : undefined,
    }
  }

  const mealTypeOptions: MealType[] = ['breakfast', 'lunch', 'snacks', 'dinner']

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50">
      <div className="fixed inset-0 bg-black/50" onClick={() => onOpenChange(false)} />
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-2xl bg-background shadow-lg flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold">Add Meal</h2>
          <button
            onClick={() => onOpenChange(false)}
            className="p-1 hover:bg-muted rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Meal type tabs */}
        <div className="flex border-b border-border px-6 pt-4">
          {mealTypeOptions.map((type) => (
            <button
              key={type}
              onClick={() => setMealType(type)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                mealType === type
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {view === 'search' && (
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Search foods..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg"
              />

              {debouncedQ.length > 0 && categories.data && (
                <div className="flex gap-2 flex-wrap">
                  {categories.data.map((cat) => (
                    <button
                      key={cat.category}
                      onClick={() =>
                        setActiveCategory(
                          activeCategory === cat.category ? undefined : cat.category
                        )
                      }
                      className={`px-3 py-1 rounded text-sm transition-colors ${
                        activeCategory === cat.category
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground hover:bg-muted/80'
                      }`}
                    >
                      {cat.category} ({cat.count})
                    </button>
                  ))}
                </div>
              )}

              {debouncedQ.length === 0 && recentFoods.data && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase">Recent</p>
                  {recentFoods.data.map((food) => (
                    <button
                      key={food.id}
                      onClick={() => {
                        setSelectedFood(food)
                        setView('detail')
                      }}
                      className="w-full text-left p-3 rounded hover:bg-muted transition-colors"
                    >
                      <p className="font-medium">{food.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {food.energy_kcal} kcal per 100g
                      </p>
                    </button>
                  ))}
                </div>
              )}

              {debouncedQ.length > 0 && (
                <div className="space-y-2">
                  {searchResults.data?.pages.flatMap((page) => page.data).map((food) => (
                    <button
                      key={food.id}
                      onClick={() => {
                        setSelectedFood(food)
                        setView('detail')
                      }}
                      className="w-full text-left p-3 rounded hover:bg-muted transition-colors"
                    >
                      <p className="font-medium">{food.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {food.category && <span>{food.category} • </span>}
                        {food.energy_kcal} kcal per 100g
                      </p>
                    </button>
                  ))}
                  <div ref={sentinelRef} />
                </div>
              )}

              {debouncedQ.length > 0 && !searchResults.data?.pages.flatMap((p) => p.data).length && !searchResults.isLoading && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No results for "{debouncedQ}"
                </p>
              )}
            </div>
          )}

          {view === 'detail' && selectedFood && (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold">{selectedFood.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {selectedFood.category && <span>{selectedFood.category}</span>}
                </p>
              </div>

              <QuantitySelector
                portions={selectedFood.portions ?? []}
                quantity={quantity}
                portionId={portionId}
                multiplier={multiplier}
                onQuantityChange={setQuantity}
                onPortionChange={setPortionId}
                onMultiplierChange={setMultiplier}
              />

              {selectedFood && (
                <div className="bg-muted p-4 rounded-lg">
                  <p className="text-xs font-semibold text-muted-foreground uppercase mb-3">Nutrition Preview</p>
                  <div className="grid grid-cols-4 gap-2">
                    {Object.entries(
                      scaleMacros(selectedFood, quantity)
                    ).map(([key, value]) => (
                      <div key={key}>
                        <p className="text-2xl font-bold">{Math.round(value as number)}</p>
                        <p className="text-xs text-muted-foreground uppercase">
                          {key === 'energy_kcal' ? 'kcal' : key[0].toUpperCase()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {view === 'image' && (
            <div className="space-y-4 flex flex-col items-center justify-center py-12">
              <div className="relative">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={extractImage.isPending}
                  className="flex flex-col items-center gap-3 px-8 py-12 border-2 border-dashed border-border rounded-lg hover:border-primary hover:bg-muted/50 transition-colors disabled:opacity-50"
                >
                  {extractImage.isPending ? (
                    <>
                      <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">Processing image...</p>
                    </>
                  ) : (
                    <>
                      <Upload className="w-8 h-8 text-muted-foreground" />
                      <div className="text-center">
                        <p className="text-sm font-medium">Click to upload</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Nutrition label or food photo
                        </p>
                      </div>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {view === 'image-detail' && imageData && (
            <div className="space-y-4">
              {imagePreview && (
                <div className="rounded-lg overflow-hidden bg-muted">
                  <img
                    src={imagePreview}
                    alt="Uploaded food"
                    className="w-full h-48 object-cover"
                  />
                </div>
              )}

              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                  {imageData.is_nutrition_label ? 'Nutrition Label' : 'Food Item'}
                </p>
                {!imageData.is_nutrition_label && imageData.food_item_name && (
                  <p className="text-sm text-foreground">{imageData.food_item_name}</p>
                )}
                {/* {!imageData.is_nutrition_label && imageData.confidence && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Confidence: {imageData.confidence}
                  </p>
                )} */}
                {!imageData.is_nutrition_label && imageData.estimation_basis && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {imageData.estimation_basis}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Quantity (g)</label>
                <input
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => {
                    const newQty = parseFloat(e.target.value) || 0
                    setQuantity(newQty)
                    // Scale macros proportionally
                    if (imageData && imageData.quantity_g) {
                      const scaled = scaleImageDataByQuantity(imageData, newQty)
                      setImageData(scaled)
                    }
                  }}
                  className="w-full px-3 py-2 border border-border rounded"
                />
              </div>

              {imageData.energy_kcal !== undefined && (
                <div className="bg-muted p-4 rounded-lg space-y-3">
                  <p className="text-xs font-semibold text-muted-foreground uppercase">
                    Extracted Nutrition (editable)
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium mb-1">Calories (kcal) *</label>
                      <input
                        type="number"
                        step="0.1"
                        value={imageData.energy_kcal || ''}
                        onChange={(e) =>
                          setImageData((p) =>
                            p ? { ...p, energy_kcal: parseFloat(e.target.value) || 0 } : null
                          )
                        }
                        className="w-full px-2 py-1 border border-border rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium mb-1">Protein (g)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={imageData.protein_g || ''}
                        onChange={(e) =>
                          setImageData((p) =>
                            p ? { ...p, protein_g: parseFloat(e.target.value) || 0 } : null
                          )
                        }
                        className="w-full px-2 py-1 border border-border rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium mb-1">Carbs (g)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={imageData.carb_g || ''}
                        onChange={(e) =>
                          setImageData((p) =>
                            p ? { ...p, carb_g: parseFloat(e.target.value) || 0 } : null
                          )
                        }
                        className="w-full px-2 py-1 border border-border rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium mb-1">Fat (g)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={imageData.fat_g || ''}
                        onChange={(e) =>
                          setImageData((p) =>
                            p ? { ...p, fat_g: parseFloat(e.target.value) || 0 } : null
                          )
                        }
                        className="w-full px-2 py-1 border border-border rounded text-sm"
                      />
                    </div>
                    {imageData.fibre_g !== undefined && (
                      <div>
                        <label className="block text-xs font-medium mb-1">Fibre (g)</label>
                        <input
                          type="number"
                          step="0.1"
                          value={imageData.fibre_g || ''}
                          onChange={(e) =>
                            setImageData((p) =>
                              p ? { ...p, fibre_g: parseFloat(e.target.value) || 0 } : null
                            )
                          }
                          className="w-full px-2 py-1 border border-border rounded text-sm"
                        />
                      </div>
                    )}
                    {imageData.sodium_mg !== undefined && (
                      <div>
                        <label className="block text-xs font-medium mb-1">Sodium (mg)</label>
                        <input
                          type="number"
                          step="0.1"
                          value={imageData.sodium_mg || ''}
                          onChange={(e) =>
                            setImageData((p) =>
                              p ? { ...p, sodium_mg: parseFloat(e.target.value) || 0 } : null
                            )
                          }
                          className="w-full px-2 py-1 border border-border rounded text-sm"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {view === 'custom' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Food Name</label>
                <input
                  type="text"
                  value={customFood.name}
                  onChange={(e) => setCustomFood((p) => ({ ...p, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded"
                  placeholder="e.g., Restaurant Biryani"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Quantity (g)</label>
                  <input
                    type="number"
                    value={customFood.quantity_g}
                    onChange={(e) =>
                      setCustomFood((p) => ({
                        ...p,
                        quantity_g: parseFloat(e.target.value) || 0,
                      }))
                    }
                    className="w-full px-3 py-2 border border-border rounded"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Calories *</label>
                  <input
                    type="number"
                    value={customFood.energy_kcal}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0
                      setCustomFood((p) => ({ ...p, energy_kcal: val }))
                    }}
                    className="w-full px-3 py-2 border border-border rounded"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium">Macros (optional)</label>
                  <button
                    onClick={handleAutoFillMacros}
                    className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/80 transition-colors"
                  >
                    Auto-fill from kcal
                  </button>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  Auto-suggested: protein 25%, carbs 45%, fat 30% — edit freely
                </p>

                <div className="grid grid-cols-3 gap-3">
                  {(
                    [
                      { key: 'protein_g', label: 'Protein (g)' },
                      { key: 'carb_g', label: 'Carbs (g)' },
                      { key: 'fat_g', label: 'Fat (g)' },
                    ] as const
                  ).map(({ key, label }) => (
                    <div key={key}>
                      <label className="block text-xs font-medium mb-1">{label}</label>
                      <input
                        type="number"
                        value={customFood[key]}
                        onChange={(e) =>
                          setCustomFood((p) => ({
                            ...p,
                            [key]: parseFloat(e.target.value) || 0,
                          }))
                        }
                        className="w-full px-2 py-1 border border-border rounded text-sm"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border px-6 py-4 space-y-2">
          {view === 'search' && (
            <>
              <button
                onClick={() => setView('image')}
                className="w-full py-2 px-4 bg-muted text-foreground rounded-lg hover:bg-muted/80 transition-colors text-sm font-medium"
              >
                Upload image
              </button>
              <button
                onClick={() => setView('custom')}
                className="w-full py-2 px-4 bg-muted text-foreground rounded-lg hover:bg-muted/80 transition-colors text-sm font-medium"
              >
                Log custom meal
              </button>
            </>
          )}

          {view === 'image' && (
            <button
              onClick={() => {
                setView('search')
                setImageData(null)
                setImagePreview(null)
              }}
              className="w-full py-2 px-4 bg-muted text-foreground rounded-lg hover:bg-muted/80 transition-colors text-sm"
            >
              Back
            </button>
          )}

          {view === 'image-detail' && (
            <>
              <button
                onClick={handleImageConfirm}
                disabled={addMeal.isPending}
                className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors font-medium"
              >
                Add to {mealType}
              </button>
              <button
                onClick={() => {
                  setView('image')
                  setImageData(null)
                  setImagePreview(null)
                }}
                className="w-full py-2 px-4 bg-muted text-foreground rounded-lg hover:bg-muted/80 transition-colors text-sm"
              >
                Back
              </button>
            </>
          )}

          {view === 'detail' && (
            <button
              onClick={handleAddLinkedMeal}
              disabled={addMeal.isPending}
              className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors font-medium"
            >
              Add to {mealType}
            </button>
          )}

          {view === 'custom' && (
            <button
              onClick={handleAddCustomMeal}
              disabled={addMeal.isPending || !customFood.name || customFood.energy_kcal === 0}
              className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors font-medium"
            >
              Add to {mealType}
            </button>
          )}

          {view !== 'search' && view !== 'image' && view !== 'image-detail' && (
            <button
              onClick={() => {
                setView('search')
                setSelectedFood(null)
              }}
              className="w-full py-2 px-4 bg-muted text-foreground rounded-lg hover:bg-muted/80 transition-colors text-sm"
            >
              Back
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

# Image Upload Feature — UI Flow Diagram

## User Journey

```
Dashboard
    ↓
[Add Meal] button clicked
    ↓
┌─────────────────────────────────────┐
│  Add Meal Drawer Opens              │
│  Meal Type: [Breakfast] [Lunch] ... │
└─────────────────────────────────────┘
    ↓
    ├──→ Search for food
    │       ↓
    │       [Search results]
    │       ↓
    │       [Detail view - quantity selector - Add to lunch]
    │
    ├──→ [Upload image] ⭐ NEW
    │       ↓
    │    ┌────────────────────────────────────┐
    │    │ 📁 Click to upload                 │
    │    │    Nutrition label or food photo   │
    │    └────────────────────────────────────┘
    │       ↓ (file selected)
    │    [⏳ Processing image...]
    │       ↓ (API completes)
    │    ┌────────────────────────────────────┐
    │    │ [Image Preview]                    │
    │    │                                    │
    │    │ Nutrition Label ✓                  │
    │    │                                    │
    │    │ Quantity (g): [100]                │
    │    │                                    │
    │    │ Extracted Nutrition (editable):    │
    │    │ ┌──────────┬──────────┐            │
    │    │ │Calories  │ 520     │ kcal │     │
    │    │ │Protein   │ 12      │  g   │     │
    │    │ │Carbs     │ 65      │  g   │     │
    │    │ │Fat       │ 18      │  g   │     │
    │    │ └──────────┴──────────┘            │
    │    │                                    │
    │    │ [Add to lunch]  [Back]             │
    │    └────────────────────────────────────┘
    │       ↓ (confirm)
    │    ✅ Meal logged
    │
    ├──→ [Log custom meal]
    │       ↓
    │       [Name, quantity, calories, macros]
    │       ↓
    │       [Add to lunch]
    │
    └──→ [Back to search]

Meal Log
    ↓
    ├── Breakfast: [list]
    ├── Lunch: [list]
    │   └── Biryani
    │       250g | 520 kcal | P:12g C:65g F:18g
    │       Source: AI 🤖
    │       → Editable  Delete
    ├── Snacks: [list]
    └── Dinner: [list]
```

## Component States

### Upload View (`view === 'image'`)
```
Content Area:
┌─────────────────────────────────┐
│  📁                             │
│  Click to upload                │
│  Nutrition label or food photo  │
└─────────────────────────────────┘

Or (loading):
┌─────────────────────────────────┐
│  ⏳ (spinning)                  │
│  Processing image...            │
└─────────────────────────────────┘

Footer:
[Back]
```

### Extraction Detail View (`view === 'image-detail'`)
```
Content Area:
[Image preview - 200px tall]

Nutrition Label ✓
(Or: Food Item - "Pav Bhaji" - Confidence: medium)

Quantity (g): [100] ← editable

Extracted Nutrition (editable):
┌─────────────┬──────────┐
│ Calories    │ [520] kcal│
│ Protein     │ [12]  g   │
│ Carbs       │ [65]  g   │
│ Fat         │ [18]  g   │
└─────────────┴──────────┘

Footer:
[Add to lunch] [Back]
```

## API Response Examples

### Nutrition Label
```json
{
  "is_nutrition_label": true,
  "quantity_g": 100,
  "energy_kcal": 520,
  "protein_g": 12,
  "carb_g": 65,
  "fat_g": 18,
  "fibre_g": null,
  "sodium_mg": null,
  "food_item_name": null,
  "confidence": null,
  "estimation_basis": null
}
```

### Food Photo
```json
{
  "is_nutrition_label": false,
  "quantity_g": 250,
  "energy_kcal": 380,
  "protein_g": 14,
  "carb_g": 48,
  "fat_g": 12,
  "fibre_g": 6,
  "sodium_mg": 620,
  "food_item_name": "Pav Bhaji, medium plate",
  "confidence": "medium",
  "estimation_basis": "Plate ~26cm, food covers 70%, typical mixed vegetable curry density"
}
```

## Keyboard Navigation

| Action | Key |
|--------|-----|
| Focus file input | `Tab` |
| Open file picker | `Enter` or `Space` |
| Navigate buttons | `Tab`, `Shift+Tab` |
| Submit | `Enter` |
| Close drawer | `Escape` |

## Mobile Considerations

- File picker adapts to mobile camera app
- Image preview scales to screen width
- Quantity input: numeric keyboard on mobile
- Buttons: full-width, 48px+ tap target
- Spinner: visible on slower connections

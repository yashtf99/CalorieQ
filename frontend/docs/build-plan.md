# CalorieQ Frontend — Incremental Build Plan

## Phase Summary

| # | Phase | Status |
|---|---|---|
| 1 | Project scaffold & tooling | ✅ Done |
| 2 | Auth — login, register, protected routes | ✅ Done |
| 3 | Layout shell + routing | ✅ Done |
| 4 | Dashboard — data layer (API hooks, types, date store) | ✅ Done |
| 5 | Dashboard — calorie ring + macro bars | 🔲 Planned |
| 6 | Dashboard — meals section | 🔲 Planned |
| 7 | Dashboard — add meal flow | 🔲 Planned |
| 8 | Dashboard — weekly chart + goal adherence | 🔲 Planned |
| 9 | Analytics page | 🔲 Planned |
| 10 | History page | 🔲 Planned |
| 11 | Profile page | 🔲 Planned |
| 12 | Polish — skeletons, errors, empty states, responsive | 🔲 Planned |

---

## Phase 1 — Project Scaffold & Tooling

### What gets built
- Vite + React + TypeScript project initialised inside `frontend/`
- All dependencies installed and configured
- Absolute imports, path aliases, and base folder structure in place
- Environment variable setup for API base URL

### Dependencies
```
# production
react react-dom react-router-dom
@tanstack/react-query axios
zustand
tailwindcss @tailwindcss/vite
shadcn/ui (init — adds components.json, cn util, base CSS vars)
recharts
react-hook-form @hookform/resolvers zod
lucide-react
date-fns

# dev
typescript @types/react @types/react-dom
prettier eslint eslint-plugin-react-hooks
```

### Folder structure
```
frontend/
├── src/
│   ├── api/          # Axios instance + per-resource query/mutation hooks
│   ├── components/   # Shared UI components
│   │   └── ui/       # shadcn-generated primitives
│   ├── pages/        # Route-level components
│   ├── store/        # Zustand slices
│   ├── lib/          # cn(), date utils, formatters
│   ├── types/        # API response/request types
│   └── main.tsx
├── .env.example      # VITE_API_BASE_URL=http://localhost:8000/api/v1
└── vite.config.ts
```

### Key config
- `vite.config.ts`: path alias `@` → `src/`
- `tailwind.config.ts`: dark mode via `class`, extend theme with CSS vars for shadcn
- `src/lib/cn.ts`: `clsx` + `tailwind-merge` utility (shadcn standard)

### Acceptance criteria
- `npm run dev` starts without errors
- `npm run build` produces a clean dist
- Tailwind utility classes apply correctly on a test component
- shadcn `Button` renders with correct dark-theme styles

---

## Phase 2 — Auth

### What gets built
- Zustand `authStore`: `accessToken`, `refreshToken`, `user`, `setTokens()`, `clearAuth()`; persisted to `localStorage`
- Axios instance (`src/api/client.ts`): base URL from env, `Authorization` header injected from store, 401 interceptor that calls `/auth/refresh`, rotates tokens, and retries the original request; on second 401 clears auth and redirects to `/login`
- `useLogin`, `useRegister`, `useLogout` mutations (TanStack Query)
- `LoginPage` and `RegisterPage` forms (React Hook Form + Zod)
- `ProtectedRoute` wrapper — redirects to `/login` if no access token
- `AuthLayout` — centered card layout for login/register

### API endpoints used
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

### Key components
| Component | Path |
|---|---|
| `LoginPage` | `pages/LoginPage.tsx` |
| `RegisterPage` | `pages/RegisterPage.tsx` |
| `ProtectedRoute` | `components/ProtectedRoute.tsx` |
| `AuthLayout` | `components/layouts/AuthLayout.tsx` |
| Axios client | `api/client.ts` |
| `authStore` | `store/authStore.ts` |

### Zod schemas
```ts
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})
const registerSchema = loginSchema.extend({
  display_name: z.string().min(1),
})
```

### Acceptance criteria
- User can register, is redirected to dashboard
- User can log in, tokens stored in Zustand + localStorage
- User can log out, tokens cleared, redirected to `/login`
- Visiting a protected route without a token redirects to `/login`
- Expired access token is silently refreshed; original request succeeds transparently
- Wrong password shows `401 Invalid email or password` inline error

---

## Phase 3 — Layout Shell + Routing

### What gets built
- Top-level router with all 4 routes wired up (all behind `ProtectedRoute`)
- `AppLayout`: top navbar + content area
- `Navbar`: CalorieQ logo, nav links (Dashboard / Analytics / History), profile avatar/dropdown with logout
- Placeholder page components for Analytics, History, Profile
- TanStack Query `QueryClient` provider at root

### Routes
```
/login              → LoginPage (public)
/register           → RegisterPage (public)
/                   → DashboardPage (protected)
/analytics          → AnalyticsPage (protected)
/history            → HistoryPage (protected)
/profile            → ProfilePage (protected)
```

### Key components
| Component | Notes |
|---|---|
| `AppLayout` | Wraps all protected pages; renders `Navbar` + `<Outlet />` |
| `Navbar` | Logo + nav links + profile dropdown |
| Placeholder pages | Each renders a heading so routing is verifiable |

### Acceptance criteria
- All 4 nav links navigate to correct pages
- Navbar highlights the active route
- Logout in profile dropdown clears auth and redirects to `/login`
- Layout renders correctly at 1280px and 1440px widths

---

## Phase 4 — Dashboard Data Layer

### What gets built
- TypeScript types for all API responses used by the dashboard (`DailySummaryOut`, `WeeklyReportOut`, `MealLogOut`, `GoalOut`)
- `dateStore` (Zustand): `selectedDate: string` (YYYY-MM-DD), `setDate()`, defaults to today; used as query key throughout dashboard
- `useDailySummary(date, tz)` — TanStack Query hook → `GET /reports/daily_summary`
- `useMealHistory(date, tz)` — `GET /meals/history?date=&tz=`
- `useWeeklyReport(weekOf, tz)` — `GET /reports/weekly`
- `useActiveGoal()` — `GET /goals/active`
- `tz` resolved once from `Intl.DateTimeFormat().resolvedOptions().timeZone` and stored in a constant; passed to all date-sensitive queries

### Types (representative)
```ts
// src/types/reports.ts
export interface DailySummaryOut {
  date: string
  goal: GoalOut | null
  consumed: { energy_kcal: number; protein_g: number; carb_g: number; fat_g: number; fibre_g: number }
  remaining: { energy_kcal: number; protein_g: number; carbs_g: number; fat_g: number } | null
  meals_tracked: number
}
```

### Acceptance criteria
- All hooks return typed data; no `any`
- Changing `selectedDate` in the store causes queries to refetch
- Network tab shows correct `date=` and `tz=` query params
- Stale data is served from cache on back-navigation; background refetch on window focus works

---

## Phase 5 — Dashboard: Calorie Ring + Macro Bars

### What gets built
- `DashboardPage` top section: greeting, `DateSelector`
- `CalorieRing`: Recharts `RadialBarChart`, shows consumed / goal kcal with centre text; green when under goal, amber when over
- `MacroCard`: four horizontal progress bars (protein, carbs, fat, fibre) — each shows `value / target g` and `%`; `null` goal renders bars without targets
- Two-column row: `CalorieRing` (left, ~40%) + `MacroCard` (right, ~60%)

### API endpoints used
- `GET /reports/daily_summary`

### Key components
| Component | Props |
|---|---|
| `DateSelector` | `date`, `onPrev`, `onNext`, `onSelect` |
| `CalorieRing` | `consumed`, `goal` (nullable) |
| `MacroBar` | `label`, `value`, `target` (nullable), `color` |
| `MacroCard` | `consumed`, `goal` (nullable) |

### Acceptance criteria
- Ring fills proportionally; capped at 100% visually (no overflow arc)
- Navigating dates with `DateSelector` updates both ring and bars
- No goal set → ring shows consumed only, bars show values without targets
- Numbers match what `GET /reports/daily_summary` returns

---

## Phase 6 — Dashboard: Meals Section

### What gets built
- `MealsSection`: full-width card, lists B/L/S/D rows
- `MealTypeRow`: expandable row per meal type showing total kcal + item count; expands to list individual food entries with name, quantity, kcal
- `DeleteMealButton`: icon button on each entry, calls `DELETE /meals/{id}`, invalidates meal history query on success
- `useDeleteMeal` mutation

### API endpoints used
- `GET /meals/history?date=&tz=`
- `DELETE /meals/{id}`

### Key components
| Component | Notes |
|---|---|
| `MealsSection` | Groups meal logs by meal_type |
| `MealTypeRow` | Collapsible; shows subtotal when collapsed |
| `MealEntryRow` | Single food item line; delete icon |

### Acceptance criteria
- All 4 meal types always render (empty ones show "No meals logged")
- Expanding a row shows each food entry with name, quantity (g), and kcal
- Deleting an entry removes it immediately (optimistic or refetch); totals update
- Meal type subtotals match the sum of their entries

---

## Phase 7 — Dashboard: Add Meal Flow

### What gets built
- `AddMealButton` (+ Add Meal) opens `AddMealDrawer` (shadcn Sheet)
- `AddMealDrawer`: meal type selector (B/L/S/D), food search input
- `FoodSearchResults`: debounced search → `GET /food_items?q=&page_size=10`; shows name, kcal/100g, source badge
- `FoodQuantityForm`: after selecting a food, shows name, quantity input (g), live-calculated kcal/protein/carbs/fat preview, "Add to [meal type]" confirm button
- `useAddMeal` mutation → `POST /meals` (linked entry with `food_item_id`); invalidates meal history + daily summary on success
- Each `MealTypeRow` also has an inline "+ Add" link that opens the drawer pre-set to that meal type

### API endpoints used
- `GET /food_items?q=&page_size=10`
- `GET /food_items/{id}` (fetch full detail + portions on selection)
- `POST /meals`

### Key components
| Component | Notes |
|---|---|
| `AddMealDrawer` | shadcn `Sheet`, slide-in from right |
| `FoodSearchInput` | 300ms debounce, clears on drawer close |
| `FoodSearchResults` | Scrollable list, loading spinner |
| `FoodQuantityForm` | Controlled quantity input, live macro preview |

### Acceptance criteria
- Search returns results within 400ms of stopping typing
- Selecting a food and entering quantity shows correct scaled macros
- Confirming adds the meal; drawer closes; meals section and calorie ring update without page reload
- Pre-opening drawer from a meal type row pre-selects that type

---

## Phase 8 — Dashboard: Weekly Chart + Goal Adherence

### What gets built
- `WeeklyCaloriesChart`: Recharts `BarChart` — 7 bars (Mon–Sun), zero-filled days included, dashed reference line at goal kcal, avg annotation
- `GoalAdherenceCard`: Mon–Sun rows with ✓ (within goal), ✗ (exceeded), or ○ (no data); "X / 7 days on target" summary
- Week automatically derived from `selectedDate` (snapped to containing Sun–Sat via `date-fns startOfWeek`)
- Two-column row below meals: `WeeklyCaloriesChart` (left) + `GoalAdherenceCard` (right)

### API endpoints used
- `GET /reports/weekly?week_of=&tz=`

### Key components
| Component | Notes |
|---|---|
| `WeeklyCaloriesChart` | Bar + reference line + avg label |
| `GoalAdherenceCard` | Day list with status icons and summary |

### Acceptance criteria
- All 7 days render; days with no logs show 0-height bar
- Reference line renders at goal kcal; absent when no goal set
- Adherence card correctly marks days ✓/✗/○
- Chart updates when `selectedDate` moves to a different week

---

## Phase 9 — Analytics Page

### What gets built
- `AnalyticsPage` with tab bar: Overview · Calories · Macros · Weight · Nutrition
- Shared `TimeRangeSelector`: buttons for 7d / 30d / 90d + custom date range picker (shadcn `Popover` + calendar)
- **Overview tab**: avg calories vs goal, avg macros vs targets, days tracked summary — data from `GET /reports/weekly` over selected range
- **Calories tab**: line chart of daily kcal over range, avg / target / variance stats
- **Macros tab**: stacked bar or grouped bar per day (protein / carbs / fat); macro distribution donut for period
- **Weight tab**: line chart from `weight_logs` in weekly report response; current / start / goal / change stats
- **Nutrition tab**: micro totals table from `GET /reports/micros`; null values shown as "—"

### API endpoints used
- `GET /reports/weekly?start=&end=&tz=`
- `GET /reports/micros?start=&end=&tz=`

### Key components
| Component | Notes |
|---|---|
| `TimeRangeSelector` | Shared across all tabs |
| `CaloriesTrendChart` | Recharts LineChart |
| `MacroStackedChart` | Recharts BarChart stacked |
| `MacroDonut` | Recharts PieChart |
| `WeightTrendChart` | Recharts LineChart |
| `MicrosTable` | Sortable table, null → "—" |

### Acceptance criteria
- All 5 tabs render without errors on empty data
- Switching time range refetches and updates all charts
- Micros tab excludes free-form entries (note displayed to user)
- Custom range respects 90-day backend cap (show error if exceeded)

---

## Phase 10 — History Page

### What gets built
- `HistoryPage`: month view — list of logged days in reverse chronological order grouped by month
- Each day row: date, total kcal, ✓/✗ vs goal, number of items logged
- Month navigation (`‹ August ›`)
- Clicking a day row sets `dateStore.selectedDate` and navigates to `/` (Dashboard)
- Data sourced by querying `GET /meals/history?start=&end=&tz=` for the visible month and aggregating client-side

### API endpoints used
- `GET /meals/history?start=&end=&tz=&page_size=200`
- `GET /goals/active` (for ✓/✗ comparison)

### Key components
| Component | Notes |
|---|---|
| `MonthNavigator` | Prev/next month, current label |
| `DayRow` | Date, kcal, goal status, item count |

### Acceptance criteria
- Only days with at least one logged meal appear
- Clicking a day navigates to Dashboard showing that day's data
- Month navigation loads correct date range

---

## Phase 11 — Profile Page

### What gets built
- `ProfilePage` with two sections: Personal Info and Goals
- **Personal Info form**: dob (date picker), gender (select), height_cm (number), activity_level (select), current_weight_kg (number); submits to `PATCH /users/me/profile`; note beneath weight field: "adds a new weight log entry"
- **Goals form**: goal_type (radio: lose / maintain / gain), daily_calories, protein_g, carbs_g, fat_g, fibre_g, weight_target_kg; submits to `POST /goals`; shows current active goal as default values
- Display name edit inline on the page header; submits to `PATCH /users/me`
- All forms use React Hook Form + Zod; validation mirrors backend constraints from `constraints.py`

### API endpoints used
- `GET /users/me`
- `PATCH /users/me`
- `GET /users/me/profile`
- `PATCH /users/me/profile`
- `GET /goals/active`
- `POST /goals`

### Key components
| Component | Notes |
|---|---|
| `PersonalInfoForm` | RHF + Zod, PATCH profile |
| `GoalsForm` | RHF + Zod, POST goal |
| `DisplayNameEditor` | Inline edit on page header |

### Zod constraint mirroring (representative)
```ts
const goalsSchema = z.object({
  goal_type: z.enum(['lose', 'maintain', 'gain']),
  daily_calories: z.number().gt(0).lt(15000).optional(),
  protein_g: z.number().gte(0).lt(1000).optional(),
  // ...
  weight_target_kg: z.number().gt(20).lt(500).optional(),
})
```

### Acceptance criteria
- Forms pre-fill from current API data
- Submitting goals creates a new versioned goal; active goal query is invalidated
- Saving weight logs a new entry (confirmed by `current_weight_kg` updating on next profile fetch)
- Validation errors display inline before any API call

---

## Phase 12 — Polish

### What gets built

**Loading states**
- Skeleton components for `CalorieRing`, `MacroCard`, `MealsSection`, `WeeklyCaloriesChart` — shown while queries are in `loading` state
- `Spinner` overlay on form submit buttons while mutations are pending

**Error states**
- `ErrorBanner` component for query errors (network failure, 5xx) with retry button
- Inline field errors on all forms

**Empty states**
- Dashboard with no goal set: soft prompt card "Set your daily goals → Profile"
- Dashboard with no meals: "No meals logged today. Add your first meal."
- Analytics with no data in range: illustrated empty state per tab
- History with no logs for month: "No meals logged in [month]"

**Responsive**
- At ≥ 1280px: two/three-column grid (as designed)
- At 1024px: collapse to two columns (calorie ring + macros stack)
- At < 1024px: single column (mobile usable but not primary target)
- Drawer/modal interactions work on all sizes

**Minor UX**
- `react-hot-toast` (or shadcn `Sonner`) for success/error toasts on mutations
- Page `<title>` updates per route
- Keyboard navigation through food search results (↑ ↓ Enter)
- Debounce all search inputs to 300ms

### Acceptance criteria
- No layout breaks between 768px and 1920px
- All data-loading states show skeletons, never blank content
- All mutations show a toast on success and on error
- App is fully usable when the backend is slow (no unhandled promise rejections, no blank screens)

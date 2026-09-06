"""
Single source of truth for all numeric constraint bounds.

Pydantic schemas use these in Field(gt=..., lt=...).
SQLAlchemy models use these in CheckConstraint(...).

These bounds are human-realistic sanity limits. They are intentionally
generous enough to accommodate unusual but legitimate food/database values,
while rejecting obvious data-entry or API errors.

Convention:
  _GT  → value must be strictly greater than this (Field gt=, SQL > )
  _GE  → value must be greater than or equal to this (Field ge=, SQL >=)
  _LT  → value must be strictly less than this (Field lt=, SQL < )
"""

# ── Meal log ──────────────────────────────────────────────────────────────────

MEAL_QUANTITY_GT    = 0
MEAL_QUANTITY_LT    = 2_000      # g — < 2 kg per meal

MEAL_ENERGY_GE      = 0
# Must be >= FOOD_ENERGY_LT * MEAL_QUANTITY_LT / 100 = 1000 * 2000 / 100 = 20,000
# to avoid DB constraint violations on high-calorie linked entries.
MEAL_ENERGY_LT      = 20_000     # kcal — covers 2kg of pure oil (worst case)

MEAL_PROTEIN_GE     = 0
MEAL_PROTEIN_LT     = 500        # g

MEAL_CARB_GE        = 0
MEAL_CARB_LT        = 1_000      # g

MEAL_FAT_GE         = 0
MEAL_FAT_LT         = 500        # g

MEAL_FIBRE_GE       = 0
MEAL_FIBRE_LT       = 200        # g

MEAL_SODIUM_GE      = 0
MEAL_SODIUM_LT      = 15_000     # mg


# ── Goal ──────────────────────────────────────────────────────────────────────

GOAL_CALORIES_GT    = 0
GOAL_CALORIES_LT    = 15_000     # kcal / day

GOAL_MACRO_GE       = 0
GOAL_MACRO_LT       = 1_000      # g / day

GOAL_WEIGHT_GT      = 20
GOAL_WEIGHT_LT      = 500        # kg


# ── Food item (per 100 g values) ──────────────────────────────────────────────

FOOD_ENERGY_GE      = 0
FOOD_ENERGY_LT      = 1_000      # kcal / 100 g
FOOD_ENERGY_KJ_GE   = 0
FOOD_ENERGY_KJ_LT   = 4_200      # kJ / 100 g

FOOD_PROTEIN_GE     = 0
FOOD_PROTEIN_LT     = 100        # g / 100 g

FOOD_CARB_GE        = 0
FOOD_CARB_LT        = 100        # g / 100 g

FOOD_FAT_GE         = 0
FOOD_FAT_LT         = 100        # g / 100 g

FOOD_FIBRE_GE       = 0
FOOD_FIBRE_LT       = 100        # g / 100 g

FOOD_SODIUM_GE      = 0
FOOD_SODIUM_LT      = 40_000     # mg / 100 g

FOOD_MINERAL_GE     = 0
FOOD_MINERAL_LT     = 10_000     # mg / 100 g

FOOD_IRON_GE        = 0
FOOD_IRON_LT        = 1_000      # mg / 100 g

FOOD_TRACE_GE       = 0
FOOD_TRACE_LT       = 1_000      # mg / 100 g

FOOD_VIT_UG_GE      = 0
FOOD_VIT_UG_LT      = 100_000    # µg / 100 g

FOOD_VIT_MG_GE      = 0
FOOD_VIT_MG_LT      = 10_000     # mg / 100 g

FOOD_CHOL_GE        = 0
FOOD_CHOL_LT        = 10_000     # mg / 100 g

FOOD_POTASSIUM_GE   = 0
FOOD_POTASSIUM_LT   = 20_000     # mg / 100 g


# ── User profile ──────────────────────────────────────────────────────────────

PROFILE_HEIGHT_GT   = 50         # cm
PROFILE_HEIGHT_LT   = 250        # cm

PROFILE_WEIGHT_GT   = 20         # kg
PROFILE_WEIGHT_LT   = 500        # kg


# ── Weight log ────────────────────────────────────────────────────────────────

WEIGHT_LOG_GT       = 20         # kg
WEIGHT_LOG_LT       = 500        # kg


# ── Food search ────────────────────────────────────────────────────────────────

FOOD_SEARCH_PAGE_SIZE_MAX = 20


# ── Reports ───────────────────────────────────────────────────────────────────

REPORT_MAX_DAYS     = 90
WEEK_START_DAY      = 6          # 6 = Sunday (Python weekday: 0=Mon … 6=Sun)
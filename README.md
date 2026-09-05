# CalorieQ
The Personal Calorie Tracker is a full-stack application designed to help users monitor, manage,
and understand their daily nutritional intake. Users can log meals across breakfast, lunch, and
dinner, set personalized health goals, and visualize macro and micronutrient trends over time.

## Functional Requirements

- Multi-User Support: Support multiple independent users who can sign up, log in, and
maintain their own private data.
- Goal Setting: Ability to set and manage personal health goals (e.g., daily calorie target,
protein/carb/fat targets, weight goal) through the web app.
- Meal Entry: Ability to create food entries grouped by meal type (Breakfast, Lunch, Dinner,
Snacks) with fields for food item name, quantity, and nutritional values (calories, macros,
micros).
- Time-Range Listing: List all food entries in a specified time range through the web app,
filterable by date and meal type.
- Nutrition Reports & Graphs: Ability to display visual reports including: weekly calorie intake
trend, macronutrient breakdown (protein, carbs, fat) by day/week, micronutrient summary
(vitamins, minerals), and goal vs. actual comparison charts.
- AI-Powered Calorie Extraction: Ability to upload a photo (product nutrition label or a plate
of food) and automatically extract and pre-fill calorie and nutritional information using AI image
analysis.
- Conversational Chat Interface: Build a chat interface powered by an LLM that allows users
to perform all app actions through natural language — logging meals, checking goals, asking
nutritional questions, and getting weekly summaries — without touching traditional UI controls
- Bulk Import via PDF: Support upload of a food diary or nutrition history exported as a PDF
(tabular format) and automatically parse and import the entries.


## Non-Functional Requirements

- Strict per-user data isolation — nutrition/health data is sensitive.
- Basic validation on nutrition values (no negative calories, sensible upper bounds) — matters since AI extraction can be noisy.
- Core meal logging and goal-setting must work even if the AI subsystem (LLM, vision model) is down — graceful degradation, not hard dependency.
- Keep AI operations async — return an immediate "processing" response and let the client poll for results, rather than blocking on a 5+ second LLM call.
- Idempotency for AI-triggered writes (re-uploading the same photo for same period shouldn't create duplicates).
- [Future] Hard per-user rate limits on AI-triggered operations (image extraction, chat) to prevent runaway costs from a single user.

# Workout Plan Generator

Generate a **personalized weekly workout plan** from your fitness goals, experience level, schedule, and equipment — powered by a Groq LLM and served with FastAPI.

## Goal

Help people get a clear, day-by-day training plan without guessing what to do each session. You describe your situation; the app calls an LLM and returns a structured weekly breakdown (warm-ups, exercises with sets/reps, rest days, and short progression notes), while respecting injuries or limitations you mention.

## What you provide

| Input | Options |
| --- | --- |
| Fitness goal | Build muscle / Lose fat / General fitness / Improve endurance |
| Experience level | Beginner / Intermediate / Advanced |
| Days per week | 1–7 |
| Equipment | No equipment / Home dumbbells / Full gym |
| Injuries or limitations *(optional)* | Free text, e.g. “bad knees”, “no overhead pressing” |

## Setup

1. **Install dependencies** (requires Python 3.13+ and [uv](https://github.com/astral-sh/uv)):

   ```bash
   uv sync
   ```

2. **Configure Groq** — get an API key from [console.groq.com/keys](https://console.groq.com/keys), then:

   ```bash
   cp .env.sample .env
   ```

   Edit `.env`:

   ```
   GROQ_API_KEY=your_key_here
   GROQ_MODEL=openai/gpt-oss-20b
   ```

   Do not commit `.env`.

## Run

```bash
uv run fastapi dev main.py
```

- **Web UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000) — fill the form and generate a plan
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

## API documentation

Base URL (local): `http://127.0.0.1:8000`

### `POST /workout-plan`

Generate a personalized weekly workout plan.

**Content-Type:** `application/json`

#### Request body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `fitness_goal` | string (enum) | Yes | One of: `Build muscle`, `Lose fat`, `General fitness`, `Improve endurance` |
| `experience_level` | string (enum) | Yes | One of: `Beginner`, `Intermediate`, `Advanced` |
| `days_per_week` | integer | Yes | Training days available per week (`1`–`7`) |
| `equipment` | string (enum) | Yes | One of: `No equipment`, `Home dumbbells`, `Full gym` |
| `injuries_or_limitations` | string or `null` | No | Free-text constraints (e.g. `"bad knees"`) |

**Example request**

```json
{
  "fitness_goal": "Build muscle",
  "experience_level": "Beginner",
  "days_per_week": 3,
  "equipment": "Home dumbbells",
  "injuries_or_limitations": "bad knees"
}
```

```bash
curl -X POST http://127.0.0.1:8000/workout-plan \
  -H "Content-Type: application/json" \
  -d "{\"fitness_goal\":\"Build muscle\",\"experience_level\":\"Beginner\",\"days_per_week\":3,\"equipment\":\"Home dumbbells\",\"injuries_or_limitations\":\"bad knees\"}"
```

#### Response `200 OK`

| Field | Type | Description |
| --- | --- | --- |
| `fitness_goal` | string | Echo of the request goal |
| `experience_level` | string | Echo of experience level |
| `days_per_week` | integer | Echo of days per week |
| `equipment` | string | Echo of equipment access |
| `injuries_or_limitations` | string or `null` | Echo of limitations, if any |
| `plan` | string | Weekly plan in Markdown (day-by-day breakdown) |

**Example response**

```json
{
  "fitness_goal": "Build muscle",
  "experience_level": "Beginner",
  "days_per_week": 3,
  "equipment": "Home dumbbells",
  "injuries_or_limitations": "bad knees",
  "plan": "## Weekly Plan\n\n### Day 1 — Full Body\n- ..."
}
```

#### Error responses

| Status | When |
| --- | --- |
| `422` | Invalid or missing body fields (validation) |
| `500` | Missing `GROQ_API_KEY` (or similar server config issue) |
| `502` | LLM returned an empty plan |

### Web UI (not in OpenAPI schema)

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | HTML form to enter preferences |
| `POST` | `/` | Same form fields as `multipart/form-data`; returns HTML with the generated plan |

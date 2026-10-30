# Workout Plan Generator

Generate a **personalized weekly workout plan** from your fitness goals, experience level, schedule, and equipment — with a Streamlit UI and a Groq LLM backend.

**Live app:** [https://workout-plan-generator-nb.streamlit.app/](https://workout-plan-generator-nb.streamlit.app/)

**Credits:** Built by Neel Bose.

## Goal

Help people get a clear, day-by-day training plan without guessing what to do each session. You describe your situation; the app calls an LLM and returns a structured weekly breakdown (warm-ups, exercises with sets/reps, rest days, and short progression notes), while respecting injuries or limitations you mention.

## Features

- Personalized weekly plan from fitness goal, experience, days/week, equipment, and optional limitations
- **Regenerate** for a different variation of the plan
- Last plan kept in **`st.session_state`** so it survives Streamlit reruns
- **Download** the plan as `.md` or `.txt`
- **Swap this exercise** — replace one exercise at a time with a suitable alternative
- Friendly error messages for invalid inputs, API failures, and empty/malformed LLM responses

## What you provide

| Input | Options |
| --- | --- |
| Fitness goal | Build muscle / Lose fat / General fitness / Improve endurance |
| Experience level | Beginner / Intermediate / Advanced |
| Days per week | 1–7 (slider) |
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

## Run locally

```bash
uv run streamlit run app.py
```

Open the local URL Streamlit prints (usually [http://localhost:8501](http://localhost:8501)).

## Deploy (Streamlit Community Cloud)

This app is hosted on [Streamlit Community Cloud](https://share.streamlit.io): [https://workout-plan-generator-nb.streamlit.app/](https://workout-plan-generator-nb.streamlit.app/)

To redeploy or recreate the app from GitHub ([KeanB24/workout-plan-generator](https://github.com/KeanB24/workout-plan-generator)):

1. Push the latest code to GitHub
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub
3. **New app** → select this repository, branch `main`, main file path `app.py`
4. Under **Advanced settings → Secrets**, add:

   ```toml
   GROQ_API_KEY = "your_key_here"
   GROQ_MODEL = "openai/gpt-oss-20b"
   ```

5. Deploy, then open the public `*.streamlit.app` URL and verify generate / regenerate / download / swap

Do not put your API key in the repo. Local `.env` and Cloud secrets are both supported.

## Project layout

| File | Role |
| --- | --- |
| `app.py` | Streamlit UI (inputs, plan display, regenerate, download, swap) |
| `workout_llm.py` | Groq prompts, plan generation, exercise swap, friendly errors |
| `.streamlit/config.toml` | Theme and client settings |

## Using the app

1. Choose your goal, experience, days per week, and equipment (and optional limitations).
2. Click **Generate plan** — the Markdown plan appears below and is stored in session state.
3. Optionally:
   - **Regenerate** — new variation with the same (current) inputs
   - **Download .md** / **Download .txt** — save the plan locally
   - **Swap this exercise** — pick one detected exercise line and replace it

## Error handling

| Situation | Behavior |
| --- | --- |
| Invalid inputs (e.g. days outside 1–7) | Friendly message; no crash |
| Bad API key, network issues, rate limits | Friendly message; no crash |
| Empty or malformed LLM response | Friendly fallback message; no crash |

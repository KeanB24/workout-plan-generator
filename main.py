import html
import os
from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from groq import Groq
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Workout Plan Generator")


class FitnessGoal(str, Enum):
    BUILD_MUSCLE = "Build muscle"
    LOSE_FAT = "Lose fat"
    GENERAL_FITNESS = "General fitness"
    IMPROVE_ENDURANCE = "Improve endurance"


class ExperienceLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class EquipmentAccess(str, Enum):
    NO_EQUIPMENT = "No equipment"
    HOME_DUMBBELLS = "Home dumbbells"
    FULL_GYM = "Full gym"


class WorkoutPlanRequest(BaseModel):
    fitness_goal: FitnessGoal
    experience_level: ExperienceLevel
    days_per_week: int = Field(..., ge=1, le=7)
    equipment: EquipmentAccess
    injuries_or_limitations: Optional[str] = Field(
        default=None,
        description="Optional constraints, e.g. 'bad knees', 'no overhead pressing'",
    )


def generate_workout_plan(
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment: str,
    injuries_or_limitations: Optional[str] = None,
) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY in environment")

    client = Groq()
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    limitations = injuries_or_limitations.strip() if injuries_or_limitations else "None"
    user_prompt = f"""Create a personalized weekly workout plan with these details:

- Fitness goal: {fitness_goal}
- Experience level: {experience_level}
- Training days per week: {days_per_week}
- Equipment: {equipment}
- Injuries / limitations: {limitations}

Requirements:
- Structure the plan as a clear day-by-day weekly breakdown (Day 1, Day 2, … plus rest days if needed).
- For each training day include: focus/theme, warm-up, exercises with sets × reps (or duration), and rest guidance.
- Respect equipment limits and any injuries/limitations.
- Match volume and intensity to the experience level and goal.
- End with a short notes section (progression tip, recovery reminder).
- Use clean Markdown with headings and bullet lists so it is easy to read.
"""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an experienced personal trainer. "
                    "Write safe, practical, personalized workout plans in clear Markdown. "
                    "Never invent medical advice; work around stated limitations."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=2500,
    )

    plan = completion.choices[0].message.content
    if not plan:
        raise HTTPException(status_code=502, detail="LLM returned an empty workout plan")

    return plan.strip()


@app.post("/workout-plan")
def create_workout_plan(body: WorkoutPlanRequest) -> dict:
    plan = generate_workout_plan(
        fitness_goal=body.fitness_goal.value,
        experience_level=body.experience_level.value,
        days_per_week=body.days_per_week,
        equipment=body.equipment.value,
        injuries_or_limitations=body.injuries_or_limitations,
    )
    return {
        "fitness_goal": body.fitness_goal.value,
        "experience_level": body.experience_level.value,
        "days_per_week": body.days_per_week,
        "equipment": body.equipment.value,
        "injuries_or_limitations": body.injuries_or_limitations,
        "plan": plan,
    }


def _options(enum_cls: type[Enum], selected: str) -> str:
    parts: list[str] = []
    for item in enum_cls:
        value = html.escape(item.value)
        sel = " selected" if item.value == selected else ""
        parts.append(f'<option value="{value}"{sel}>{value}</option>')
    return "\n".join(parts)


def _render_page(
    *,
    fitness_goal: str = FitnessGoal.BUILD_MUSCLE.value,
    experience_level: str = ExperienceLevel.BEGINNER.value,
    days_per_week: int = 3,
    equipment: str = EquipmentAccess.FULL_GYM.value,
    injuries_or_limitations: str = "",
    plan: Optional[str] = None,
    error: Optional[str] = None,
) -> HTMLResponse:
    error_html = (
        f'<div class="error">{html.escape(error)}</div>' if error else ""
    )

    if plan:
        notes = (
            f" · Notes: {html.escape(injuries_or_limitations)}"
            if injuries_or_limitations.strip()
            else ""
        )
        plan_html = f"""
    <section class="plan" aria-live="polite">
      <h2>Your weekly plan</h2>
      <p class="meta">
        {html.escape(fitness_goal)} · {html.escape(experience_level)} ·
        {days_per_week} day(s)/week · {html.escape(equipment)}{notes}
      </p>
      <div class="plan-body">{html.escape(plan)}</div>
    </section>
"""
    else:
        plan_html = ""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Workout Plan Generator</title>
  <style>
    :root {{
      --bg: #0f1419;
      --surface: #1a222c;
      --border: #2d3a47;
      --text: #e8eef4;
      --muted: #8b9aab;
      --accent: #3d9a6a;
      --accent-hover: #4cb87e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", system-ui, sans-serif;
      background: radial-gradient(ellipse at top, #1a2a22 0%, var(--bg) 55%);
      color: var(--text);
      line-height: 1.5;
    }}
    main {{
      max-width: 920px;
      margin: 0 auto;
      padding: 2rem 1.25rem 3rem;
    }}
    h1 {{ margin: 0 0 0.35rem; font-size: 1.85rem; letter-spacing: -0.02em; }}
    .subtitle {{ color: var(--muted); margin: 0 0 1.75rem; }}
    form {{
      display: grid;
      gap: 1rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem 1.35rem;
    }}
    label {{ display: grid; gap: 0.4rem; font-size: 0.9rem; font-weight: 600; }}
    .hint {{ font-weight: 400; color: var(--muted); font-size: 0.8rem; }}
    select, input[type="number"], textarea {{
      width: 100%;
      padding: 0.65rem 0.75rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      font: inherit;
    }}
    textarea {{ min-height: 72px; resize: vertical; }}
    .row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }}
    @media (max-width: 640px) {{ .row {{ grid-template-columns: 1fr; }} }}
    button {{
      justify-self: start;
      margin-top: 0.25rem;
      padding: 0.7rem 1.25rem;
      border: none;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }}
    button:hover {{ background: var(--accent-hover); }}
    .plan {{
      margin-top: 1.75rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.35rem 1.5rem;
    }}
    .plan h2 {{
      margin: 0 0 1rem;
      font-size: 1.15rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--border);
    }}
    .plan-body {{ white-space: pre-wrap; font-size: 0.95rem; }}
    .meta {{
      color: var(--muted);
      font-size: 0.85rem;
      margin-bottom: 1rem;
    }}
    .error {{
      margin-top: 1rem;
      padding: 0.85rem 1rem;
      border-radius: 8px;
      background: #3a1f24;
      border: 1px solid #7a3a45;
      color: #ffc9d0;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Workout Plan Generator</h1>
    <p class="subtitle">Tell us your goals and schedule — get a personalized weekly plan.</p>

    <form method="post" action="/">
      <div class="row">
        <label>
          Fitness goal
          <select name="fitness_goal" required>
            {_options(FitnessGoal, fitness_goal)}
          </select>
        </label>
        <label>
          Experience level
          <select name="experience_level" required>
            {_options(ExperienceLevel, experience_level)}
          </select>
        </label>
      </div>

      <div class="row">
        <label>
          Days available per week
          <span class="hint">1–7</span>
          <input type="number" name="days_per_week" min="1" max="7"
                 value="{days_per_week}" required />
        </label>
        <label>
          Equipment access
          <select name="equipment" required>
            {_options(EquipmentAccess, equipment)}
          </select>
        </label>
      </div>

      <label>
        Injuries or limitations <span class="hint">(optional)</span>
        <textarea name="injuries_or_limitations"
          placeholder="e.g. bad knees, no overhead pressing">{html.escape(injuries_or_limitations)}</textarea>
      </label>

      <button type="submit">Generate plan</button>
    </form>

    {error_html}
    {plan_html}
  </main>
</body>
</html>
"""
    return HTMLResponse(page)


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return _render_page()


@app.post("/", response_class=HTMLResponse)
def index_generate(
    fitness_goal: str = Form(...),
    experience_level: str = Form(...),
    days_per_week: int = Form(...),
    equipment: str = Form(...),
    injuries_or_limitations: str = Form(""),
) -> HTMLResponse:
    form_kwargs = dict(
        fitness_goal=fitness_goal,
        experience_level=experience_level,
        days_per_week=days_per_week,
        equipment=equipment,
        injuries_or_limitations=injuries_or_limitations,
    )
    try:
        if not 1 <= days_per_week <= 7:
            raise ValueError("Days per week must be between 1 and 7.")
        if fitness_goal not in {g.value for g in FitnessGoal}:
            raise ValueError("Invalid fitness goal.")
        if experience_level not in {e.value for e in ExperienceLevel}:
            raise ValueError("Invalid experience level.")
        if equipment not in {e.value for e in EquipmentAccess}:
            raise ValueError("Invalid equipment option.")

        plan = generate_workout_plan(
            fitness_goal=fitness_goal,
            experience_level=experience_level,
            days_per_week=days_per_week,
            equipment=equipment,
            injuries_or_limitations=injuries_or_limitations or None,
        )
        return _render_page(**form_kwargs, plan=plan)
    except HTTPException as exc:
        return _render_page(**form_kwargs, error=str(exc.detail))
    except ValueError as exc:
        return _render_page(**form_kwargs, error=str(exc))

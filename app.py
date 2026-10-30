"""Streamlit UI for personalized workout plan generation."""

from __future__ import annotations

import streamlit as st

from workout_llm import (
    EQUIPMENT_OPTIONS,
    EXPERIENCE_LEVELS,
    FITNESS_GOALS,
    WorkoutPlanError,
    extract_exercises,
    generate_workout_plan,
    swap_exercise,
)

st.set_page_config(
    page_title="Workout Plan Generator",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

:root {
  --ink: #12201a;
  --muted: #5c6f66;
  --panel: #ffffff;
  --line: #d5e0d9;
  --accent: #1f7a4d;
  --accent-soft: #e4f3ea;
  --accent-deep: #145c38;
}

html, body, [class*="css"]  {
  font-family: "DM Sans", sans-serif;
}

.stApp {
  background:
    radial-gradient(ellipse 90% 55% at 12% -8%, #d9efe3 0%, transparent 55%),
    radial-gradient(ellipse 70% 40% at 100% 0%, #e7f1ea 0%, transparent 48%),
    linear-gradient(180deg, #f7faf8 0%, #eef3f0 100%);
  color: var(--ink);
}

#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
div[data-testid="stToolbar"] { display: none; }

.block-container {
  max-width: 900px;
  padding-top: 1.6rem;
  padding-bottom: 3.25rem;
}

.hero {
  margin: 0.25rem 0 1.35rem 0;
}
.hero h1 {
  font-family: "Fraunces", Georgia, serif !important;
  font-size: clamp(2rem, 4vw, 2.55rem) !important;
  font-weight: 700 !important;
  line-height: 1.15 !important;
  letter-spacing: -0.02em;
  color: var(--ink) !important;
  margin: 0 0 0.5rem 0 !important;
}
.hero p {
  margin: 0;
  max-width: 38rem;
  color: var(--muted);
  font-size: 1.04rem;
  line-height: 1.55;
}

.section-label {
  font-family: "Fraunces", Georgia, serif;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--ink);
  margin: 0 0 0.2rem 0;
}
.section-help {
  color: var(--muted);
  font-size: 0.92rem;
  margin: 0 0 0.85rem 0;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 0.15rem 0 0.95rem 0;
}
.meta-chip {
  display: inline-flex;
  align-items: center;
  background: var(--accent-soft);
  color: var(--accent-deep);
  border: 1px solid #c5e2d1;
  border-radius: 999px;
  padding: 0.28rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
}

div[data-testid="stForm"] {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.15rem 1.2rem 1rem;
  box-shadow: 0 12px 28px rgba(18, 32, 26, 0.06);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--panel);
  border: 1px solid var(--line) !important;
  border-radius: 18px !important;
  box-shadow: 0 12px 28px rgba(18, 32, 26, 0.05);
}

.plan-body {
  background: linear-gradient(180deg, #fbfdfc 0%, #f4f9f6 100%);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.85rem 1.15rem 0.35rem;
  margin-top: 0.35rem;
}
.plan-body h1, .plan-body h2, .plan-body h3 {
  font-family: "Fraunces", Georgia, serif !important;
  color: var(--ink) !important;
  letter-spacing: -0.01em;
}
.plan-body h1 { font-size: 1.4rem !important; margin-top: 0.15rem !important; }
.plan-body h2 {
  font-size: 1.12rem !important;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0.3rem;
  margin-top: 1.2rem !important;
}
.plan-body li { color: #24352c; }

.stSlider [data-baseweb="slider"] div[role="slider"] {
  background-color: var(--accent) !important;
}

div.stButton > button,
div.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button {
  border-radius: 10px !important;
  font-weight: 600 !important;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}
div.stButton > button:hover,
div.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(31, 122, 77, 0.18);
}

.empty-hint {
  background: #fff7ec;
  color: #8a4b12;
  border: 1px solid #f0d3ad;
  border-radius: 14px;
  padding: 0.95rem 1.05rem;
  font-size: 0.95rem;
  margin-top: 0.35rem;
}

.app-footer {
  margin-top: 2.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.88rem;
  text-align: center;
}
.app-footer strong {
  color: var(--ink);
  font-weight: 600;
}
</style>
"""


def _init_state() -> None:
    defaults = {
        "plan": None,
        "saved_inputs": None,
        "generate_error": None,
        "swap_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _save_plan(plan: str, inputs: dict) -> None:
    st.session_state.plan = plan
    st.session_state.saved_inputs = inputs
    st.session_state.generate_error = None
    st.session_state.swap_error = None


def _current_inputs() -> dict:
    injuries = st.session_state.get("injuries_or_limitations") or ""
    return {
        "fitness_goal": st.session_state.fitness_goal,
        "experience_level": st.session_state.experience_level,
        "days_per_week": st.session_state.days_per_week,
        "equipment": st.session_state.equipment,
        "injuries_or_limitations": injuries.strip() or None,
    }


def _run_generate(*, regenerate: bool) -> None:
    inputs = _current_inputs()
    st.session_state.swap_error = None
    try:
        with st.spinner(
            "Building your weekly plan…" if not regenerate else "Creating a new variation…"
        ):
            plan = generate_workout_plan(**inputs, regenerate=regenerate)
        _save_plan(plan, inputs)
    except WorkoutPlanError as exc:
        st.session_state.generate_error = str(exc)
    except Exception:
        st.session_state.generate_error = (
            "Something went wrong while generating the plan. Please try again."
        )


def _run_swap(exercise_line: str) -> None:
    plan = st.session_state.plan
    inputs = st.session_state.saved_inputs or _current_inputs()
    st.session_state.generate_error = None
    if not plan:
        st.session_state.swap_error = "Generate a plan before swapping an exercise."
        return
    try:
        with st.spinner("Swapping exercise…"):
            updated = swap_exercise(
                plan,
                exercise_line,
                fitness_goal=inputs["fitness_goal"],
                experience_level=inputs["experience_level"],
                equipment=inputs["equipment"],
                injuries_or_limitations=inputs.get("injuries_or_limitations"),
            )
        _save_plan(updated, inputs)
        st.toast("Exercise swapped")
    except WorkoutPlanError as exc:
        st.session_state.swap_error = str(exc)
    except Exception:
        st.session_state.swap_error = (
            "Something went wrong while swapping the exercise. Please try again."
        )


def _meta_chips(inputs: dict) -> str:
    chips: list[str] = []
    mapping = [
        inputs.get("fitness_goal"),
        inputs.get("experience_level"),
        f"{inputs.get('days_per_week')} days/week" if inputs.get("days_per_week") else None,
        inputs.get("equipment"),
    ]
    if inputs.get("injuries_or_limitations"):
        mapping.append(f"Notes: {inputs['injuries_or_limitations']}")
    for item in mapping:
        if item:
            chips.append(f'<span class="meta-chip">{item}</span>')
    return f'<div class="meta-row">{"".join(chips)}</div>'


_init_state()
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
      <h1>Workout Plan Generator</h1>
      <p>Tell us your goal, schedule, and gear — get a clear day-by-day weekly plan you can regenerate, download, or tweak one exercise at a time.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("workout_form"):
    st.markdown(
        '<p class="section-label">Your preferences</p>'
        '<p class="section-help">These shape volume, exercise selection, and weekly structure.</p>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.selectbox("Fitness goal", FITNESS_GOALS, key="fitness_goal")
        st.slider(
            "Days available per week",
            min_value=1,
            max_value=7,
            value=3,
            key="days_per_week",
        )
    with col2:
        st.selectbox("Experience level", EXPERIENCE_LEVELS, key="experience_level")
        st.selectbox("Equipment access", EQUIPMENT_OPTIONS, key="equipment")

    st.text_area(
        "Injuries or limitations (optional)",
        placeholder="e.g. bad knees, no overhead pressing",
        key="injuries_or_limitations",
        height=88,
    )
    generate_clicked = st.form_submit_button(
        "Generate plan",
        type="primary",
        use_container_width=True,
    )

if generate_clicked:
    _run_generate(regenerate=False)

if st.session_state.generate_error:
    st.error(st.session_state.generate_error)

plan = st.session_state.plan
if plan:
    with st.container(border=True):
        st.markdown(
            '<p class="section-label">Your weekly plan</p>'
            '<p class="section-help">Kept in this session — regenerate or download anytime.</p>',
            unsafe_allow_html=True,
        )
        inputs = st.session_state.saved_inputs or {}
        st.markdown(_meta_chips(inputs), unsafe_allow_html=True)

        action_cols = st.columns(3, gap="small")
        with action_cols[0]:
            if st.button("Regenerate", use_container_width=True, help="Get a different variation"):
                _run_generate(regenerate=True)
                st.rerun()
        with action_cols[1]:
            st.download_button(
                "Download .md",
                data=plan,
                file_name="workout-plan.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with action_cols[2]:
            st.download_button(
                "Download .txt",
                data=plan,
                file_name="workout-plan.txt",
                mime="text/plain",
                use_container_width=True,
            )

        st.markdown('<div class="plan-body">', unsafe_allow_html=True)
        st.markdown(plan)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    with st.container(border=True):
        st.markdown(
            '<p class="section-label">Swap this exercise</p>'
            '<p class="section-help">Replace one move with a similar alternative that fits your gear and limits.</p>',
            unsafe_allow_html=True,
        )
        exercises = extract_exercises(plan)
        if not exercises:
            st.info("No swappable exercise lines were detected in this plan.")
        else:
            selected = st.selectbox("Exercise to swap", exercises, key="exercise_to_swap")
            if st.button("Swap selected exercise", use_container_width=True):
                _run_swap(selected)
                st.rerun()
        if st.session_state.swap_error:
            st.error(st.session_state.swap_error)
else:
    st.markdown(
        '<div class="empty-hint">Set your preferences above, then generate a plan to see a day-by-day breakdown here.</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="app-footer">Built by <strong>Neel Bose</strong></div>',
    unsafe_allow_html=True,
)

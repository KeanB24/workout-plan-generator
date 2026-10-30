"""Groq-backed workout plan generation helpers for the Streamlit app."""

from __future__ import annotations

import os
import re
from typing import Optional

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    Groq,
    RateLimitError,
)

load_dotenv()


def _apply_streamlit_secrets() -> None:
    """Copy Streamlit Cloud secrets into env when present (local .env still wins if set)."""
    try:
        import streamlit as st
    except ImportError:
        return
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in ("GROQ_API_KEY", "GROQ_MODEL"):
        if os.getenv(key):
            continue
        try:
            value = secrets.get(key)
        except Exception:
            value = None
        if value:
            os.environ[key] = str(value)

FITNESS_GOALS = (
    "Build muscle",
    "Lose fat",
    "General fitness",
    "Improve endurance",
)
EXPERIENCE_LEVELS = ("Beginner", "Intermediate", "Advanced")
EQUIPMENT_OPTIONS = ("No equipment", "Home dumbbells", "Full gym")

FRIENDLY_EMPTY_PLAN = (
    "We couldn't build a usable workout plan from the AI response. "
    "Please try again in a moment."
)
FRIENDLY_API_FAILURE = (
    "We couldn't reach the workout planner right now. "
    "Please check your connection and try again shortly."
)
FRIENDLY_AUTH_FAILURE = (
    "The workout planner isn't configured correctly (API key). "
    "Please check GROQ_API_KEY and try again."
)
FRIENDLY_RATE_LIMIT = (
    "Too many requests right now. Please wait a moment and try again."
)
FRIENDLY_SWAP_FAILURE = (
    "We couldn't swap that exercise right now. Please try again."
)


class WorkoutPlanError(Exception):
    """User-facing error with a friendly message."""


def _is_usable_plan(plan: str) -> bool:
    text = plan.strip()
    if len(text) < 80:
        return False
    lowered = text.lower()
    has_day_structure = any(
        marker in lowered
        for marker in ("day 1", "day 2", "## day", "### day", "monday", "workout")
    )
    has_exercise_cue = any(
        marker in lowered
        for marker in ("sets", "reps", "warm-up", "warmup", "rest", "exercise")
    )
    return has_day_structure and has_exercise_cue


def _extract_text_from_message(message: object) -> str:
    """Prefer message content; fall back to reasoning for models that spend tokens there."""
    content = getattr(message, "content", None)
    if content and str(content).strip():
        return str(content).strip()

    reasoning = getattr(message, "reasoning", None)
    if reasoning and str(reasoning).strip():
        # Often ends with the intended one-line answer in quotes or as the last line.
        text = str(reasoning).strip()
        quoted = re.findall(r'["“]([^"”]+)["”]', text)
        if quoted:
            return quoted[-1].strip()
        for line in reversed(text.splitlines()):
            cleaned = line.strip().strip("\"'` ")
            cleaned = re.sub(r"^(?:so\s+)?(?:answer|output|result)\s*[:=]\s*", "", cleaned, flags=re.I)
            if len(cleaned) >= 8 and not cleaned.lower().startswith(("we ", "the user", "i ")):
                return cleaned
    return ""


def _chat(messages: list[dict[str, str]], *, temperature: float, max_tokens: int) -> str:
    _apply_streamlit_secrets()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise WorkoutPlanError(FRIENDLY_AUTH_FAILURE)

    client = Groq()
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except AuthenticationError as exc:
        raise WorkoutPlanError(FRIENDLY_AUTH_FAILURE) from exc
    except RateLimitError as exc:
        raise WorkoutPlanError(FRIENDLY_RATE_LIMIT) from exc
    except (APIConnectionError, APITimeoutError) as exc:
        raise WorkoutPlanError(FRIENDLY_API_FAILURE) from exc
    except APIStatusError as exc:
        raise WorkoutPlanError(FRIENDLY_API_FAILURE) from exc
    except Exception as exc:
        raise WorkoutPlanError(FRIENDLY_API_FAILURE) from exc

    try:
        message = completion.choices[0].message
    except (AttributeError, IndexError, TypeError) as exc:
        raise WorkoutPlanError(FRIENDLY_EMPTY_PLAN) from exc

    text = _extract_text_from_message(message)
    if not text:
        raise WorkoutPlanError(FRIENDLY_EMPTY_PLAN)

    return text


def _build_plan_prompt(
    *,
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment: str,
    injuries_or_limitations: Optional[str],
    regenerate: bool,
) -> str:
    limitations = injuries_or_limitations.strip() if injuries_or_limitations else "None"
    variation = ""
    if regenerate:
        variation = (
            "\nCreate a meaningfully different variation from a typical plan for these "
            "inputs (different split, exercise choices, or weekly structure) while still "
            "meeting the requirements.\n"
        )

    return f"""Create a personalized weekly workout plan with these details:

- Fitness goal: {fitness_goal}
- Experience level: {experience_level}
- Training days per week: {days_per_week}
- Equipment: {equipment}
- Injuries / limitations: {limitations}
{variation}
Requirements:
- Structure the plan as a clear day-by-day weekly breakdown (Day 1, Day 2, … plus rest days if needed).
- For each training day include: focus/theme, warm-up, exercises with sets × reps (or duration), and rest guidance.
- Respect equipment limits and any injuries/limitations.
- Match volume and intensity to the experience level and goal.
- End with a short notes section (progression tip, recovery reminder).
- Use clean Markdown with headings and bullet lists (NOT tables).
- Format each exercise as a bullet like: `- Push-ups: 3 sets × 10 reps, rest 60s`
"""


def generate_workout_plan(
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment: str,
    injuries_or_limitations: Optional[str] = None,
    *,
    regenerate: bool = False,
) -> str:
    if not 1 <= days_per_week <= 7:
        raise WorkoutPlanError("Please choose between 1 and 7 training days per week.")
    if fitness_goal not in FITNESS_GOALS:
        raise WorkoutPlanError("Please choose a valid fitness goal.")
    if experience_level not in EXPERIENCE_LEVELS:
        raise WorkoutPlanError("Please choose a valid experience level.")
    if equipment not in EQUIPMENT_OPTIONS:
        raise WorkoutPlanError("Please choose a valid equipment option.")

    prompt = _build_plan_prompt(
        fitness_goal=fitness_goal,
        experience_level=experience_level,
        days_per_week=days_per_week,
        equipment=equipment,
        injuries_or_limitations=injuries_or_limitations,
        regenerate=regenerate,
    )
    temperature = 0.95 if regenerate else 0.7

    plan_text = _chat(
        [
            {
                "role": "system",
                "content": (
                    "You are an experienced personal trainer. "
                    "Write safe, practical, personalized workout plans in clear Markdown. "
                    "Use bullet lists for exercises, never Markdown tables. "
                    "Never invent medical advice; work around stated limitations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=4000,
    )

    if not _is_usable_plan(plan_text):
        raise WorkoutPlanError(FRIENDLY_EMPTY_PLAN)

    return plan_text


_BULLET_EXERCISE = re.compile(
    r"""^\s*(?:[-*•]|\d+[.)])\s+
        (?!\*\*(?:form|tip|rest|sleep|nutrition|progression|recovery|active)\b)
        (.+)$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Markdown table row: | **Name** | 3 × 10 | 90 s |
_TABLE_EXERCISE = re.compile(
    r"""^\|\s*
        (?:\*\*)?(?P<name>[^|*]+?)(?:\*\*)?\s*\|
        \s*(?P<sets>[^|]*?(?:\d\s*[×x]\s*\d|sets?|reps?)[^|]*)\|
        \s*(?P<rest>[^|]+)\|?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_SKIP_TABLE_NAMES = {
    "exercise",
    "warmup",
    "warm-up",
    "warm up",
    "sets × reps",
    "sets x reps",
    "rest",
}

# Deterministic substitutions when the LLM swap fails
_LOCAL_SWAPS = {
    "push-up": "Kneeling push-ups",
    "push up": "Kneeling push-ups",
    "pushups": "Kneeling push-ups",
    "bench press": "Floor press",
    "overhead press": "Arnold press",
    "squat": "Goblet squat",
    "lunge": "Reverse lunge",
    "deadlift": "Romanian deadlift",
    "row": "Renegade row",
    "curl": "Hammer curl",
    "plank": "Dead bug",
    "crunch": "Glute bridge",
    "lateral raise": "Front raise",
    "pull-up": "Inverted row",
    "pull up": "Inverted row",
    "burpee": "Mountain climbers",
}


def _normalize_spaces(text: str) -> str:
    return re.sub(r"[\s\u00a0\u202f\u2007\u2009\u2011‑]+", " ", text).strip()


def _strip_md(text: str) -> str:
    text = _normalize_spaces(text)
    text = re.sub(r"\*+", "", text)
    return text.strip(" |-")


def _looks_like_work(text: str) -> bool:
    lowered = text.lower()
    if any(
        bad in lowered
        for bad in (
            "form first",
            "progression",
            "nutrition",
            "recovery reminder",
            "sleep:",
            "hydrate",
            "rest days",
            "tip:",
        )
    ):
        return False
    return bool(
        re.search(r"\d\s*[×x]\s*\d", lowered)
        or re.search(r"\bsets?\b", lowered)
        or re.search(r"\breps?\b", lowered)
    )


def extract_exercises(plan: str) -> list[str]:
    """Pull exercise entries from bullet lists or Markdown tables."""
    found: list[str] = []
    seen: set[str] = set()

    for line in plan.splitlines():
        raw = line.rstrip()
        label: Optional[str] = None

        table = _TABLE_EXERCISE.match(raw)
        if table:
            name = _strip_md(table.group("name"))
            sets = _normalize_spaces(table.group("sets"))
            if name.lower() in _SKIP_TABLE_NAMES or set(name) <= set("-:"):
                continue
            if not _looks_like_work(f"{name} {sets}"):
                continue
            label = _normalize_spaces(f"{name}: {sets}")
        else:
            bullet = _BULLET_EXERCISE.match(raw)
            if bullet:
                text = _strip_md(bullet.group(1))
                if _looks_like_work(text):
                    label = text

        if label and label not in seen:
            seen.add(label)
            found.append(label)

    return found


def _find_plan_line(plan: str, exercise_label: str) -> Optional[str]:
    """Return the original plan line that corresponds to a picker label."""
    target = _normalize_spaces(exercise_label).lower()
    # Label may be "Name: sets" from a table
    name_part = target.split(":", 1)[0].strip()

    for line in plan.splitlines():
        norm_line = _normalize_spaces(_strip_md(line)).lower()
        if target and target in norm_line:
            return line
        if name_part and len(name_part) >= 4 and name_part in norm_line and _looks_like_work(norm_line):
            # Prefer table/bullet rows that also carry the sets cue from the label
            if ":" in target:
                sets_part = target.split(":", 1)[1].strip()
                if sets_part and _normalize_spaces(sets_part).lower() in norm_line:
                    return line
            else:
                return line
    return None


def _local_replacement(exercise_label: str) -> str:
    """Build a non-LLM substitute that keeps sets/reps when possible."""
    text = _strip_md(exercise_label)
    name, sep, trailing = text.partition(":")
    if not sep:
        # e.g. "Push-ups — 3 sets × 10" or "Push-ups 3×10"
        m = re.match(r"^(.*?)(\s+[—\-–]?\s*\d.*)$", text)
        if m:
            name, trailing = m.group(1), m.group(2)
            sep = ":"
        else:
            name, trailing, sep = text, " 3 sets × 10 reps", ":"

    name_l = name.lower()
    new_name = None
    for key, alt in _LOCAL_SWAPS.items():
        if key in name_l and alt.lower() not in name_l:
            new_name = alt
            break
    if not new_name:
        new_name = f"Modified {name.strip()}"

    trailing = trailing.strip()
    if trailing:
        return _normalize_spaces(f"{new_name}: {trailing}")
    return _normalize_spaces(new_name)


def _apply_replacement(plan: str, original_line: str, replacement: str) -> str:
    """Replace one plan line, preserving bullets or table structure."""
    replacement = _normalize_spaces(re.sub(r"^[-*•]\s+", "", replacement.strip().strip(" \"'")))
    new_lines: list[str] = []
    swapped = False
    for line in plan.splitlines():
        if swapped or line != original_line:
            new_lines.append(line)
            continue

        table = _TABLE_EXERCISE.match(line)
        if table:
            # Keep sets/rest cells; swap the exercise name.
            name = replacement.split(":", 1)[0].strip()
            name = re.sub(r"\s+\d.*$", "", name).strip() or replacement
            sets = table.group("sets").strip()
            rest = table.group("rest").strip()
            new_lines.append(f"| **{name}** | {sets} | {rest} |")
        else:
            prefix_match = re.match(r"^(\s*(?:[-*•]|\d+[.)])\s+)", line)
            prefix = prefix_match.group(1) if prefix_match else ""
            new_lines.append(f"{prefix}{replacement}")
        swapped = True

    if not swapped:
        raise WorkoutPlanError("That exercise is no longer in the current plan.")
    return "\n".join(new_lines)


def swap_exercise(
    plan: str,
    exercise_line: str,
    *,
    fitness_goal: str,
    experience_level: str,
    equipment: str,
    injuries_or_limitations: Optional[str] = None,
) -> str:
    """Replace one exercise in the plan with a suitable alternative."""
    original_line = _find_plan_line(plan, exercise_line)
    if not original_line:
        raise WorkoutPlanError("That exercise is no longer in the current plan.")

    limitations = injuries_or_limitations.strip() if injuries_or_limitations else "None"
    prompt = (
        f"Replace this exercise with one different alternative.\n"
        f"Goal: {fitness_goal}. Level: {experience_level}. Equipment: {equipment}. "
        f"Limits: {limitations}.\n"
        f"Original: {exercise_line}\n"
        f"Reply with ONE line only like 'Exercise name: 3 sets × 10 reps'. "
        f"No bullets, quotes, or explanation."
    )

    replacement = None
    try:
        replacement = _chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You suggest safe exercise substitutions. "
                        "Output exactly one replacement exercise line."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=800,
        )
        replacement = replacement.splitlines()[0].strip()
        replacement = re.sub(r"^[-*•]\s+", "", replacement)
        replacement = replacement.strip(" \"'")
        replacement = _normalize_spaces(replacement)
        if (
            not replacement
            or _normalize_spaces(replacement).lower()
            == _normalize_spaces(exercise_line).lower()
        ):
            replacement = None
    except WorkoutPlanError:
        replacement = None

    if not replacement:
        replacement = _local_replacement(exercise_line)

    return _apply_replacement(plan, original_line, replacement)

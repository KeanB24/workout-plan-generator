# ch1 — FastAPI Intro

Two FastAPI examples: a static joke endpoint and an LLM-powered joke generator via Groq.

## Setup

### 🔑 Getting a Groq API key

You only need to do this once.

1. Go to **[console.groq.com](https://console.groq.com/keys)** and sign up — email, Google, or GitHub all work. No credit card needed.
2. In the left sidebar, click **API Keys** → **Create API Key**.
3. Give it a name (e.g. `my-groq-key`) and click **Create**.
4. **Copy the key immediately** — Groq shows it to you exactly once. If you lose it, you'll have to create a new one.
5. Paste it into your `.env` file (copy `.env.sample` to `.env` first):
   ```
   GROQ_API_KEY=your_key_here
   ```
6. Never commit `.env` to git or paste your key into a shared notebook cell, this project's `.gitignore` already excludes it, keep it that way.

### 🔄 Syncing dependencies

```bash
uv sync
```

## Scripts

### 1. Static Jokes (`1_get_joke.py`)

Returns a random hardcoded joke.

```bash
uv run fastapi dev 1_get_joke.py
```

`GET http://localhost:8000/joke`

---

### 2. AI-Generated Jokes (`2_generate_jokes.py`)

Generates a joke on any topic using Groq.

**Configure env:**

```bash
cp .env.sample .env
# fill in GROQ_API_KEY and GROQ_MODEL in .env
```

```bash
uv run fastapi dev 2_generate_jokes.py
```

`GET http://localhost:8000/joke?topic=python`

---

Interactive docs available at `http://localhost:8000/docs`.

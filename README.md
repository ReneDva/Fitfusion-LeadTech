# 💪 FitFusion — AI Fitness & Nutrition Platform

FitFusion is a local, Python-only AI fitness ecosystem: AI Body Analysis, an AI-generated
workout plan that can be adapted on the fly by an AI Coach (back pain, missing equipment,
short on time — without touching your saved plan), a Workout Tracker with per-exercise
demo videos and live rep/calorie tracking, an AI Nutrition Center (photo/barcode/manual food
logging), an AI Coach chat, a Progress dashboard, achievements, and a Premium tier preview —
all in one dark, gold/blue/green "glass" themed app that also works fully in Arabic and
Hebrew (RTL).

Built with **[Streamlit](https://streamlit.io)** so the entire UI is written in Python — no
HTML/CSS/JavaScript required to run or modify it. Data is stored locally in a SQLite file;
the only network calls are optional (Google Gemini, for AI Coach / workout adaptation /
meal-photo recognition, and the free OpenFoodFacts API for barcode lookups).

---

## 1. Requirements

- **Python 3.10 or newer** — check with `python --version`
- A free [Google Gemini API key](https://aistudio.google.com/apikey) is optional (only needed
  for AI Coach chat, AI workout adaptation, meal-photo recognition, and AI-written
  body-analysis summaries — everything else works fully offline with a rule-based fallback)
- No webcam needed — the Workout Tracker uses a manual rep/timer counter plus a curated
  YouTube demo video per exercise (see Roadmap for why live webcam pose-tracking isn't wired up)

## 2. Setup

Open a terminal in this folder and run:

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure your AI key (optional but recommended)

Create a `.env` file in this folder (there's no `.env.example` template — just create it)
with:

```
GEMMINI_API_KEY=your-key-here
```

This one key is shared by every user of this local instance — nobody is asked to enter their
own key inside the app. Leave it unset and the app runs in offline/rule-based mode: body
analysis, workout plans, workout adaptation, and food search/barcode/manual logging all still
work; AI Coach chat gives canned evidence-based tips instead of live LLM answers, workout
adaptation falls back to a rule-based swap/trim engine, and meal-photo recognition is disabled
with an on-screen note.

## 3. Run it

```bash
streamlit run app.py
```

Your browser opens automatically at **http://localhost:8501**. If it doesn't, open that URL
manually. Stop the app anytime with `Ctrl+C` in the terminal.

On first run, a `fitfusion.db` SQLite file is created in this folder — that's your entire
local database (users, profiles, meals, workouts, chat history, progress). Delete it to reset
the app to a clean slate.

## 4. Using the app

1. **Sign in or sign up** — the app opens directly on this screen. A language picker
   (English / العربية / עברית) sits above the tabs so the page renders correctly RTL even
   before you have an account. The Sign Up tab shows a short "what you get" benefits list;
   the Login tab stays minimal.
2. **Profile Setup** — height, weight, age, activity level, goal, equipment, preferred
   language, etc. This immediately triggers your first **AI Body Analysis** and generates
   your first **AI Workout Plan**.
3. Use the **sidebar** to navigate: Body Analysis, Workouts, Workout Tracker, Nutrition, AI Coach,
   Progress, Profile, Premium. Language preference now lives on the **Profile** page (and the
   sign-in page), not the sidebar — the sidebar just shows your account + logout.
4. On the **Workouts** page, each day has two buttons: **Start Workout**, and **💬 Adapt with
   AI Coach** — describe a constraint ("my back hurts today", "no dumbbells", "short on
   time") and the AI Coach rewrites *just that session* (never your saved weekly plan),
   guaranteeing it never reintroduces an exercise already in that day.
5. In the **Workout Tracker**, each exercise shows its target sets/reps/rest next to a manual
   rep counter (or a timer, in 5-second steps, for held exercises like planks) and a curated
   demo video. The calorie estimate updates live as you count reps/seconds — it's driven by
   what you actually did, not a guess — and finishing a session with some exercises
   skipped/incomplete shows an honest partial-completion percentage with an encouraging
   message instead of a false "100% complete" celebration.

## 5. Project structure

```
app.py                  # Entry point: auth (login/signup) / profile setup / dashboard
pages/                   # One file per section — Streamlit turns these into the sidebar nav
fitfusion/
  config.py              # Brand colors, constants, env loading
  i18n.py                # Language detection + translation lookup
  db.py                  # SQLite schema + all read/write helpers
  auth.py                # Password hashing, signup/login
  calculations.py        # BMI / BMR / TDEE / macros / body type / metabolic score formulas
  ai.py                  # Shared-key Google Gemini integration (chat, workout adaptation,
                          # meal photo, narratives) with rule-based offline fallbacks
  workout_engine.py       # Rule-based AI workout plan generator + session-only AI adaptation
  nutrition_engine.py     # Local food DB search + OpenFoodFacts barcode lookup + scoring
  videos.py               # Curated per-exercise YouTube demo links + search-link fallback
  charts.py               # Progress rings / line / bar / donut chart builders
  styles.py               # Dark/glass/gold design system (CSS injection + card components,
                          # incl. mobile-responsive sidebar/stat-card rules)
  achievements.py         # Achievement/badge rules
  nav.py                  # Shared sidebar + login guard + language picker used across pages
data/
  translations/{en,ar,he}.json
  exercises.json, exercise_videos.json, foods.json
```

> `fitfusion/pose_detection.py` (mediapipe + streamlit-webrtc live rep counter) and the
> corresponding `opencv-python-headless` / `mediapipe` / `streamlit-webrtc` / `av` entries in
> `requirements.txt` are no longer imported anywhere — the trainer page (now "Workout
> Tracker") was simplified to a
> manual counter. They're left in place rather than deleted in case live pose tracking comes
> back; safe to strip out if you want a lighter install.

## 6. Multi-language

English, Arabic (اَلْعَرَبِيَّة, RTL) and Hebrew (עברית, RTL) are fully supported. Pick a language
right on the sign-in page (before you even have an account) or later from the Profile page —
both choices persist to your saved profile. The AI Coach, workout adaptation, recipes, and
body-analysis narratives reply in your selected language (naturally localized, not
machine-translated), when AI features are enabled.

## 7. Deploying for testing (Streamlit Community Cloud)

To let others try the app over a URL instead of running it locally, deploy to
[Streamlit Community Cloud](https://share.streamlit.io) — free, and it handles Python +
Streamlit for you. Two things Cloud needs that aren't automatic:

**Dependencies**

- `requirements.txt` — already present, installed automatically via pip.
- `packages.txt` — apt-level system lib `opencv-python` needs on Cloud's Linux box
  (`libgl1`). Already present.

**Secrets**
`.env` is never committed (gitignored) and Cloud doesn't read it. Instead, paste the same
key/value pairs into the app's **Settings → Secrets** box in TOML format:

```toml
GEMMINI_API_KEY = "your-key-here"
GEMINI_MODEL = "gemini-flash-lite-latest"
```

Rotate the key before sharing the deployed URL if it was ever used locally in a shared `.env`.

**Deploy steps**

1. Push this repo to GitHub (`main` branch).
2. Sign in to [share.streamlit.io](https://share.streamlit.io) with GitHub, authorize the repo.
3. "Create app" → pick this repo, branch `main`, main file path `app.py`.
4. Advanced settings → Secrets → paste the block above.
5. Deploy.

**Known limitations on Cloud**

- `fitfusion.db` (SQLite) lives on Cloud's ephemeral filesystem — it resets on every reboot
  or redeploy. Fine for a testing pass; not for data anyone needs to keep.

---

## Roadmap / known simplifications

This is a full local build of the FitFusion product spec, with a few things intentionally
simplified for a **local, Python-only, no-payment-processor app**:

| Area                                               | In this build                                                                                                                        | Full spec                                                                                                                                        |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Google / Apple sign-in                             | Shown, explains it needs a registered OAuth app                                                                                      | Real OAuth                                                                                                                                       |
| Premium checkout                                   | UI preview, toggles your local plan flag                                                                                             | Real payment processor (Stripe/App Store/Play)                                                                                                   |
| Workout Tracker                                    | Manual rep/timer counter next to a curated YouTube demo per exercise; calorie estimate computed live from reps/seconds actually done | Live webcam pose detection + automatic rep counting (code exists in`pose_detection.py` but is currently disconnected — see Project structure) |
| Bottom navigation                                  | Streamlit sidebar (collapses to a ☰ menu on narrow screens, tuned for mobile width/wrapping)                                        | Fixed mobile bottom tab bar                                                                                                                      |
| Notifications                                      | In-app only, per-session toggle                                                                                                      | OS push notifications (needs a native/mobile shell + push service)                                                                               |
| Wearable sync (Apple Health, Fitbit, Garmin, etc.) | Not connected                                                                                                                        | Real device SDK integrations                                                                                                                     |
| AI Coach / workout adaptation / meal recognition   | Real Gemini calls when`GEMMINI_API_KEY` is set; rule-based fallback otherwise (never blocks the app)                               | Same, always-on                                                                                                                                  |

These are natural next steps if this app were wrapped in a native mobile shell (e.g. with
Capacitor/Flutter) or given a real backend + payment provider — the data model in `db.py` was
kept generic enough to support that without a rewrite.

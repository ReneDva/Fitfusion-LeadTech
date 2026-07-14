# 💪 FitFusion — AI Fitness & Nutrition Platform

FitFusion is a local, Python-only AI fitness ecosystem: AI Body Analysis, an AI-generated
workout plan, a 3D exercise trainer with live webcam rep-counting, an AI Nutrition Center
(photo/barcode/manual food logging), an AI Coach chat, a Progress dashboard, achievements,
and a Premium tier preview — all in one dark, gold/blue/green "glass" themed app.

Built with **[Streamlit](https://streamlit.io)** so the entire UI is written in Python — no
HTML/CSS/JavaScript required to run or modify it. Data is stored locally in a SQLite file;
the only network calls are optional (Google Gemini, for AI Coach / meal-photo recognition, and
the free OpenFoodFacts API for barcode lookups).

---

## 1. Requirements

- **Python 3.10 or newer** — check with `python --version`
- A webcam is optional (only needed for the live 3D Trainer rep counter)
- A free [Google Gemini API key](https://aistudio.google.com/apikey) is optional (only needed
  for AI Coach chat, meal-photo recognition, and AI-written body-analysis summaries —
  everything else works fully offline)

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

> If `mediapipe` / `streamlit-webrtc` / `opencv-python` fail to install (rare, usually on very
> new Python versions or unsupported architectures), that's fine — skip them and everything
> still runs. The 3D Trainer page automatically falls back to a manual rep counter with a
> clear on-screen notice instead of crashing.

### Configure your AI key (optional but recommended)

Copy the example env file and add your key:

**Windows:**
```powershell
copy .env.example .env
```
**macOS / Linux:**
```bash
cp .env.example .env
```

Then open `.env` in any text editor and set:
```
GEMMINI_API_KEY=your-key-here
```

This one key is shared by every user of this local instance — nobody is asked to enter their
own key inside the app. Leave it unset and the app runs in offline/rule-based mode: body
analysis, workout plans, and food search/barcode/manual logging all still work; AI Coach chat
gives canned evidence-based tips instead of live LLM answers, and meal-photo recognition is
disabled with an on-screen note.

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

1. **Splash → Onboarding** — auto-plays on first load.
2. **Sign up** with a name / email / username / password (local accounts — see Roadmap below
   for social login).
3. **Profile Setup** — height, weight, age, activity level, goal, equipment, etc. This
   immediately triggers your first **AI Body Analysis** and generates your first **AI
   Workout Plan**.
4. Use the **sidebar** (☰ menu icon top-left on mobile widths) to navigate: Body Analysis,
   Workouts, 3D Trainer, Nutrition, AI Coach, Progress, Profile, Premium.
5. In the **3D Trainer**, pick an exercise to see a rotatable animated 3D demo (drag to spin
   it). If your machine has a webcam and the optional camera dependencies installed, click
   **Start Live Form Check** to get live pose-skeleton overlay + automatic rep counting; your
   browser will ask for camera permission the first time.

## 5. Project structure

```
app.py                  # Entry point: splash / onboarding / auth / profile setup / dashboard
pages/                   # One file per section — Streamlit turns these into the sidebar nav
fitfusion/
  config.py              # Brand colors, constants, env loading
  i18n.py                # Language detection + translation lookup
  db.py                  # SQLite schema + all read/write helpers
  auth.py                # Password hashing, signup/login
  calculations.py        # BMI / BMR / TDEE / macros / body type / metabolic score formulas
  ai.py                  # Shared-key Google Gemini integration (chat, meal photo, narratives)
  workout_engine.py       # Rule-based AI workout plan generator
  nutrition_engine.py     # Local food DB search + OpenFoodFacts barcode lookup + scoring
  pose_detection.py       # mediapipe + streamlit-webrtc live rep counter
  skeleton3d.py           # Procedural 3D stick-figure exercise animations (Plotly)
  charts.py               # Progress rings / line / bar / donut chart builders
  styles.py               # Dark/glass/gold design system (CSS injection + card components)
  achievements.py         # Achievement/badge rules
  nav.py                  # Shared sidebar + login guard used by every page
data/
  translations/{en,ar,he}.json
  exercises.json, foods.json
```

## 6. Multi-language

English, Arabic (اَلْعَرَبِيَّة, RTL) and Hebrew (עברית, RTL) are fully supported, auto-detected
from your OS locale on first load, and switchable anytime from the sidebar. The AI Coach,
recipes, and body-analysis narratives reply in your selected language (naturally localized,
not machine-translated), when AI features are enabled.

---

## Roadmap / known simplifications

This is a full local build of the FitFusion product spec, with a few things intentionally
simplified for a **local, Python-only, no-payment-processor app**:

| Area | In this build | Full spec |
|---|---|---|
| Google / Apple sign-in | Shown, explains it needs a registered OAuth app | Real OAuth |
| Premium checkout | UI preview, toggles your local plan flag | Real payment processor (Stripe/App Store/Play) |
| 3D Personal Trainer | Real, rotatable, animated 3D stick-figure demos generated from code + **real** mediapipe pose detection & rep counting via webcam | Photorealistic rigged 3D character |
| Bottom navigation | Streamlit sidebar (collapses to a ☰ menu on narrow screens) | Fixed mobile bottom tab bar |
| Notifications | In-app only, per-session toggle | OS push notifications (needs a native/mobile shell + push service) |
| Wearable sync (Apple Health, Fitbit, Garmin, etc.) | Not connected | Real device SDK integrations |
| Meal recognition / AI Coach | Real Gemini vision + chat calls when `GEMMINI_API_KEY` is set; rule-based fallback otherwise | Same, always-on |

These are natural next steps if this app were wrapped in a native mobile shell (e.g. with
Capacitor/Flutter) or given a real backend + payment provider — the data model in `db.py` was
kept generic enough to support that without a rewrite.

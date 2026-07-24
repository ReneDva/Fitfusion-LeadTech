import streamlit as st

from fitfusion.i18n import t, current_language
from fitfusion.nav import require_login
from fitfusion.styles import section_title, glass_card, stat_card, empty_state
from fitfusion.charts import macro_donut
from fitfusion import db, ai, nutrition_engine as nut

st.set_page_config(page_title=f"{t('nutrition_title')} · FitFusion", page_icon="🥗", layout="centered")
user = require_login()
profile = db.get_profile(user["id"])

st.title(f"🥗 {t('nutrition_title')}")

if "pending_meal" not in st.session_state:
    st.session_state["pending_meal"] = None

subscription = db.get_subscription(user["id"])
is_premium = bool(subscription and subscription["plan"] == "premium")

tabs = st.tabs([
    f"📷 {t('take_photo')}", f"📤 {t('upload_image')}", f"📝 {t('describe_meal')}",
    f"🔍 {t('scan_barcode')}", f"🔎 {t('search_food')}", f"🍱 {t('build_meal')}",
])

# --- Photo (Premium only) ---------------------------------------------------
with tabs[0]:
    if not is_premium:
        st.info(f"✨ {t('photo_premium_notice')}")
        st.page_link("pages/8_✨_Premium.py", label=t("premium_title"), icon="✨")
    else:
        photo = st.camera_input(t("take_photo"), label_visibility="collapsed")
        if photo and st.button(f"🧠 {t('analyze')}", type="primary", key="analyze_photo_btn"):
            if not ai.ai_enabled():
                st.info(t("ai_disabled_notice"))
            else:
                with st.spinner(t("loading_ai")):
                    result = ai.analyze_meal_photo(photo.getvalue(), current_language())
                if "error" in result:
                    st.error(f"Couldn't analyze this photo ({result['error']}). Try Build Meal Manually instead.")
                else:
                    result["source"] = "ai_photo"
                    st.session_state["pending_meal"] = result

# --- Upload (Premium only) ----------------------------------------------------
with tabs[1]:
    if not is_premium:
        st.info(f"✨ {t('photo_premium_notice')}")
        st.page_link("pages/8_✨_Premium.py", label=t("premium_title"), icon="✨")
    else:
        upload = st.file_uploader(t("upload_image"), type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if upload and st.button(f"🧠 {t('analyze')}", type="primary", key="analyze_upload_btn"):
            if not ai.ai_enabled():
                st.info(t("ai_disabled_notice"))
            else:
                with st.spinner(t("loading_ai")):
                    result = ai.analyze_meal_photo(upload.getvalue(), current_language())
                if "error" in result:
                    st.error(f"Couldn't analyze this image ({result['error']}). Try Build Meal Manually instead.")
                else:
                    result["source"] = "ai_photo"
                    st.session_state["pending_meal"] = result

# --- Describe Meal (free, text-based) -----------------------------------------
with tabs[2]:
    description = st.text_area(t("describe_meal"), placeholder=t("describe_meal_placeholder"), label_visibility="collapsed")
    if description and st.button(f"🧠 {t('analyze')}", type="primary", key="analyze_text_btn"):
        if not ai.ai_enabled():
            st.info(t("ai_disabled_notice"))
        else:
            with st.spinner(t("loading_ai")):
                result = ai.analyze_meal_text(description, current_language())
            if "error" in result:
                st.error(f"Couldn't analyze this description ({result['error']}). Try Build Meal Manually instead.")
            else:
                result["source"] = "ai_text"
                st.session_state["pending_meal"] = result

# --- Barcode -------------------------------------------------------------------
with tabs[3]:
    barcode = st.text_input(t("scan_barcode"), placeholder="e.g. 737628064502")
    if st.button(f"🔍 {t('look_up')}", type="primary") and barcode:
        with st.spinner("Looking up product..."):
            result = nut.lookup_barcode(barcode)
        if "error" in result:
            st.error(f"Product not found ({result['error']}). Try Search Food instead.")
        else:
            st.session_state["pending_meal"] = result

# --- Search ----------------------------------------------------------------
with tabs[4]:
    query = st.text_input(t("search_food"), placeholder="e.g. chicken, rice, banana / עוף, אורז / دجاج, أرز")
    results = nut.search_food(query) if query else []
    if results:
        chosen_food = st.selectbox(
            t("search_results"), results, format_func=lambda f: nut.display_name(f, current_language())
        )
        grams = st.slider(t("grams_label"), 10, 500, 100, step=10)
        if st.button(f"➕ {t('use_this_food')}", type="primary"):
            st.session_state["pending_meal"] = nut.scale_to_grams(chosen_food, grams, current_language())
    elif query:
        st.caption(t("no_local_matches"))

# --- Build Meal --------------------------------------------------------------
with tabs[5]:
    picked = st.multiselect(t("add_foods"), nut.FOODS, format_func=lambda f: nut.display_name(f, current_language()))
    items = []
    for food in picked:
        grams = st.slider(f"{nut.display_name(food, current_language())} ({t('g')})", 10, 500, 100, step=10, key=f"grams_{food['name']}")
        items.append(nut.scale_to_grams(food, grams, current_language()))
    if items and st.button(f"🍱 {t('build_this_meal')}", type="primary"):
        st.session_state["pending_meal"] = nut.aggregate_meal(items)

# --- Pending meal review -----------------------------------------------------
pending = st.session_state.get("pending_meal")
if pending:
    st.divider()
    section_title("🧾", pending.get("name", "Meal"))
    if "quality_score" not in pending:
        pending["quality_score"] = nut.meal_quality_score(pending)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("calories_label"), f"{round(pending.get('calories', 0))} {t('kcal')}")
    c2.metric(t("protein"), f"{round(pending.get('protein', 0))}{t('g')}")
    c3.metric(t("carbs"), f"{round(pending.get('carbs', 0))}{t('g')}")
    c4.metric(t("fat"), f"{round(pending.get('fat', 0))}{t('g')}")

    c5, c6, c7 = st.columns(3)
    c5.metric(t("fiber"), f"{round(pending.get('fiber', 0))}{t('g')}")
    c6.metric(t("sugar"), f"{round(pending.get('sugar', 0))}{t('g')}")
    c7.metric(t("sodium"), f"{round(pending.get('sodium', 0))} mg")

    st.progress(pending["quality_score"] / 100, text=f"{t('meal_quality_score')}: {pending['quality_score']}/100")

    alt = pending.get("healthier_alternative") or nut.healthier_alternative(pending)
    glass_card(f"🌿 <b>{t('healthier_alternatives')}:</b> {alt}", glow="green")
    if pending.get("category"):
        st.caption(f"{t('portion_suggestion')}: {nut.suggested_portion(pending, profile['fitness_goal'] or 'general_health')}")

    if st.button(f"✅ {t('log_meal')}", type="primary", width='stretch'):
        db.log_meal(user["id"], pending)
        st.session_state["pending_meal"] = None
        st.success(t("success_saved"))
        st.rerun()

# --- Today's meals -------------------------------------------------------------
st.divider()
section_title("📆", t("todays_meals"))
meals = db.meals_for_date(user["id"])
if not meals:
    empty_state(t("empty_no_data"))
else:
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for m in meals:
        for k in totals:
            totals[k] += m[k]
        glass_card(
            f"<b>{m['name']}</b><br><span style='color:#B3B3B3'>{round(m['calories'])} {t('kcal')} · "
            f"{t('protein')} {round(m['protein'])}{t('g')} · {t('carbs')} {round(m['carbs'])}{t('g')} · {t('fat')} {round(m['fat'])}{t('g')} · "
            f"{t('meal_quality_score')} {m['quality_score']}/100</span>"
        )
    st.plotly_chart(macro_donut(totals["protein"], totals["carbs"], totals["fat"]), width='stretch', config={"displayModeBar": False})

# --- Recipe generator ------------------------------------------------------------
st.divider()
section_title("👨‍🍳", t("generate_recipe"))
recipe_prompt = st.text_input(t("recipe_prompt_label"), placeholder="e.g. chicken, spinach, high protein dinner")
if st.button(t("generate_recipe"), width='stretch') and recipe_prompt:
    with st.spinner(t("loading_ai")):
        recipe = ai.generate_recipe(recipe_prompt, profile["dietary_preference"] or "none", current_language())
    glass_card(recipe.replace("\n", "<br>"), glow="gold")

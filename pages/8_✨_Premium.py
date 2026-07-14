import streamlit as st

from fitfusion.i18n import t
from fitfusion.nav import require_login
from fitfusion.styles import glass_card
from fitfusion import db

st.set_page_config(page_title=f"{t('premium_title')} · FitFusion", page_icon="✨", layout="centered")
user = require_login()

st.markdown(f"<h1 style='text-align:center'>✨ {t('premium_title')}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;color:#B3B3B3'>{t('premium_subtitle')}</p>", unsafe_allow_html=True)

benefits = [t(f"premium_benefit_{i}") for i in range(1, 9)]
cols = st.columns(2)
for i, benefit in enumerate(benefits):
    with cols[i % 2]:
        glass_card(f"⭐ {benefit}", glow="gold")

st.divider()
plan_choice = st.radio(" ", [t("monthly"), t("annual")], horizontal=True, label_visibility="collapsed")
price = "$9.99 / mo" if plan_choice == t("monthly") else "$79.99 / yr  (save 33%)"
st.markdown(f"<h2 style='text-align:center;color:#F4B223'>{price}</h2>", unsafe_allow_html=True)

st.info(t("premium_coming_soon"))

c1, c2 = st.columns(2)
with c1:
    if st.button(t("free_trial"), use_container_width=True, type="primary"):
        db.set_subscription(user["id"], "premium")
        st.success(t("success_saved"))
        st.balloons()
        st.rerun()
with c2:
    if st.button(t("manage_subscription"), use_container_width=True):
        db.set_subscription(user["id"], "free")
        st.success(t("success_saved"))
        st.rerun()

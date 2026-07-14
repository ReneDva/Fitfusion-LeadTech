"""FitFusion design system: global CSS injection + reusable glass/gold component renderers.

Streamlit generates the page's HTML/CSS/JS itself — this module only supplies extra CSS
(scoped, no external assets) and small HTML snippets for cards. No hand-written page
templates are needed anywhere else in the app.
"""
import base64

import streamlit as st

from fitfusion.config import GOLD, BLUE, BG, CARD_BG, BG_SECONDARY, TEXT_SECONDARY, APP_NAME, ASSETS_DIR
from fitfusion.i18n import is_rtl

LOGO_PATH = ASSETS_DIR / "fitfusion-logo.png"
_logo_b64_cache = None
_logo_thumb_b64_cache = None


def _logo_base64() -> str:
    global _logo_b64_cache
    if _logo_b64_cache is None:
        _logo_b64_cache = base64.b64encode(LOGO_PATH.read_bytes()).decode() if LOGO_PATH.exists() else ""
    return _logo_b64_cache


def _logo_thumb_base64(size: int = 96) -> str:
    """Small resized copy for the sidebar — avoids shipping the full-res PNG on every page nav."""
    global _logo_thumb_b64_cache
    if _logo_thumb_b64_cache is None and LOGO_PATH.exists():
        import io
        from PIL import Image
        img = Image.open(LOGO_PATH).convert("RGB")
        img.thumbnail((size, size))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        _logo_thumb_b64_cache = base64.b64encode(buf.getvalue()).decode()
    return _logo_thumb_b64_cache or ""


def inject_global_css():
    direction = "rtl" if is_rtl() else "ltr"
    text_align = "right" if is_rtl() else "left"
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            direction: {direction};
        }}
        .stApp {{
            background: radial-gradient(circle at 20% 0%, #151515 0%, {BG} 55%) fixed;
            color: #FFFFFF;
        }}
        [data-testid="stSidebar"] {{
            background: {BG_SECONDARY};
            border-{'left' if is_rtl() else 'right'}: 1px solid rgba(244,178,35,0.15);
        }}
        h1, h2, h3, h4 {{
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            text-align: {text_align};
        }}
        p, span, label, li {{ text-align: {text_align}; }}
        #MainMenu, footer {{ visibility: hidden; }}
        [data-testid="stAppDeployButton"] {{ display: none !important; }}
        [data-testid="stSidebarNav"] input {{ display: none !important; }}

        .ff-glass {{
            background: rgba(21, 21, 21, 0.75);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 22px;
            padding: 20px 22px;
            margin-bottom: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.35);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .ff-glass:hover {{ transform: translateY(-2px); box-shadow: 0 12px 34px rgba(0,0,0,0.45); }}

        .ff-glow-gold {{ box-shadow: 0 0 28px rgba(244,178,35,0.35), 0 8px 30px rgba(0,0,0,0.35); border-color: rgba(244,178,35,0.35); }}
        .ff-glow-blue {{ box-shadow: 0 0 28px rgba(76,183,197,0.30), 0 8px 30px rgba(0,0,0,0.35); border-color: rgba(76,183,197,0.35); }}
        .ff-glow-green {{ box-shadow: 0 0 28px rgba(139,197,63,0.30), 0 8px 30px rgba(0,0,0,0.35); border-color: rgba(139,197,63,0.35); }}

        .ff-stat-icon {{ font-size: 26px; margin-bottom: 6px; }}
        .ff-stat-value {{ font-size: 26px; font-weight: 800; margin: 2px 0; }}
        .ff-stat-label {{ font-size: 12.5px; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.04em; }}

        .ff-badge {{
            display: inline-block; padding: 3px 12px; border-radius: 999px;
            font-size: 11.5px; font-weight: 700; letter-spacing: 0.03em;
        }}
        .ff-title-row {{ display:flex; align-items:center; gap:10px; margin: 6px 0 14px 0; }}
        .ff-emoji-xl {{ font-size: 34px; }}

        .stButton > button {{
            border-radius: 16px !important;
            font-weight: 700 !important;
            padding: 0.6rem 1.2rem !important;
            border: none !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }}
        .stButton > button:hover {{ transform: translateY(-1px) scale(1.01); }}
        .stButton > button:active {{ transform: scale(0.97); }}
        div[data-testid="stFormSubmitButton"] > button,
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {GOLD}, #ffcf6b) !important;
            color: #1a1200 !important;
            box-shadow: 0 6px 22px rgba(244,178,35,0.35) !important;
        }}
        .stButton > button[kind="secondary"] {{
            background: {CARD_BG} !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
        }}

        [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea, .stSelectbox > div > div {{
            background-color: {CARD_BG} !important;
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            color: #FFFFFF !important;
        }}

        [data-testid="stChatMessage"] {{
            background: rgba(21,21,21,0.75);
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.06);
        }}

        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(244,178,35,0.35); border-radius: 8px; }}

        @keyframes ff-pulse {{ 0% {{ opacity: 0.5; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.5; }} }}
        .ff-pulse {{ animation: ff-pulse 1.6s ease-in-out infinite; }}

        @keyframes ff-pop {{ 0% {{ transform: scale(0.6); opacity: 0; }} 60% {{ transform: scale(1.08); }} 100% {{ transform: scale(1); opacity: 1; }} }}
        .ff-pop {{ animation: ff-pop 0.5s ease-out; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def app_shell_open():
    inject_global_css()


def glass_card(body_html: str, glow: str = "") -> None:
    glow_class = f"ff-glow-{glow}" if glow else ""
    # A blank/whitespace-only line here would end Streamlit's raw-HTML block early
    # (CommonMark), leaking the closing </div> as visible text. Strip them.
    cleaned = "\n".join(line for line in body_html.splitlines() if line.strip())
    st.markdown(f'<div class="ff-glass {glow_class} ff-pop">{cleaned}</div>', unsafe_allow_html=True)


def stat_card(icon: str, label: str, value: str, color: str = GOLD, sub: str = "") -> None:
    sub_html = f'<div class="ff-stat-label" style="margin-top:4px;opacity:0.8">{sub}</div>' if sub else ""
    glass_card(
        f"""
        <div class="ff-stat-icon">{icon}</div>
        <div class="ff-stat-value" style="color:{color}">{value}</div>
        <div class="ff-stat-label">{label}</div>
        {sub_html}
        """
    )


def section_title(icon: str, text: str) -> None:
    st.markdown(f'<div class="ff-title-row"><span class="ff-emoji-xl">{icon}</span><h3 style="margin:0">{text}</h3></div>', unsafe_allow_html=True)


def badge(text: str, color: str = GOLD) -> str:
    return f'<span class="ff-badge" style="background:{color}22;color:{color};border:1px solid {color}55">{text}</span>'


def empty_state(text: str, icon: str = "🌱") -> None:
    glass_card(f'<div style="text-align:center;padding:20px 0"><div style="font-size:40px">{icon}</div><p style="color:{TEXT_SECONDARY};margin-top:8px">{text}</p></div>')


def ai_thinking(text: str) -> None:
    st.markdown(f'<div class="ff-pulse" style="color:{BLUE};font-weight:600">🧠 {text}</div>', unsafe_allow_html=True)


def gold_glow_logo(size_px: int = 120) -> str:
    b64 = _logo_base64()
    inner = (
        f'<img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;border-radius:32px" />'
        if b64 else "💪"
    )
    background = "transparent" if b64 else f"linear-gradient(135deg,{GOLD},#ffcf6b)"
    return f"""
    <div style="display:flex;justify-content:center;padding:24px 0">
      <div style="
        width:{size_px}px;height:{size_px}px;border-radius:32px;
        display:flex;align-items:center;justify-content:center;overflow:hidden;
        background:{background};
        box-shadow:0 0 60px rgba(244,178,35,0.55), 0 0 120px rgba(244,178,35,0.25);
        font-size:{int(size_px*0.5)}px;">{inner}</div>
    </div>
    """


def sidebar_logo_html() -> str:
    b64 = _logo_thumb_base64()
    if not b64:
        return f"<h3>💪 {APP_NAME}</h3>"
    return f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
      <img src="data:image/png;base64,{b64}" style="width:36px;height:36px;border-radius:10px;object-fit:cover" />
      <span style="font-size:19px;font-weight:800">{APP_NAME}</span>
    </div>
    """

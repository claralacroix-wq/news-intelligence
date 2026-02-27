import streamlit as st
from collector import fetch_newsapi, fetch_rss, enrich_with_metadata, fetch_trending_topics, fetch_stock_data
from analyzer import analyze_articles
from digest import fetch_full_digest, CATEGORY_LABELS
from datetime import datetime
import json, os

SAVED_TOPICS_FILE = os.path.join(os.path.dirname(__file__), "saved_topics.json")

def load_saved_topics():
    if os.path.exists(SAVED_TOPICS_FILE):
        try:
            with open(SAVED_TOPICS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_topics_to_file(topics):
    with open(SAVED_TOPICS_FILE, "w") as f:
        json.dump(topics, f)

st.set_page_config(page_title="The Brief — News Intelligence", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400;1,700&family=Source+Sans+3:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { background: #f5f0e8 !important; color: #1a1410 !important; font-family: 'Source Serif 4', serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── HEADER ── */
.site-header { background: #1a1410; padding: 20px 48px; display: flex; align-items: center; justify-content: space-between; }
.site-logo-wrap { text-align: center; flex: 1; }
.site-logo { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 900; color: #f5f0e8; letter-spacing: -1px; line-height: 1; display: inline-block; }
.site-logo em { color: #c1440e; font-style: normal; }
.site-tagline { font-family: 'Source Sans 3', sans-serif; font-size: 10px; letter-spacing: 3px; color: #6b5d50; text-transform: uppercase; margin-top: 3px; }
.site-date { font-family: 'Source Sans 3', sans-serif; font-size: 11px; color: #4a3d32; line-height: 1.8; min-width: 140px; }
.site-left { min-width: 140px; }
.red-stripe { background: #c1440e; height: 4px; }

/* ── MARKET TICKER ── */
.ticker-bar { background: #1a1410; border-top: 1px solid #2a2018; padding: 6px 48px; display: flex; gap: 32px; overflow-x: auto; flex-wrap: nowrap; }
.ticker-item { display: flex; align-items: center; gap: 8px; white-space: nowrap; flex-shrink: 0; }
.ticker-name { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #6b5d50; text-transform: uppercase; }
.ticker-price { font-family: 'Source Sans 3', sans-serif; font-size: 12px; font-weight: 700; color: #f5f0e8; }
.ticker-up { color: #4caf78 !important; font-size: 11px; font-weight: 700; }
.ticker-down { color: #e05a3a !important; font-size: 11px; font-weight: 700; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] { gap: 0; background: transparent; padding: 0 48px; border-bottom: 1px solid #d9d0c4; margin-top: 0; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #8a7a6a !important; border: none !important; border-bottom: 3px solid transparent !important; font-family: 'Source Sans 3', sans-serif !important; font-size: 11px !important; font-weight: 700 !important; letter-spacing: 2px !important; text-transform: uppercase !important; padding: 12px 20px !important; margin-right: 2px; border-radius: 0 !important; }
.stTabs [aria-selected="true"] { background: #c1440e !important; color: #fff !important; border-bottom: 3px solid #c1440e !important; }
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) { background: #ede5d8 !important; color: #1a1410 !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* ── BUTTONS ── */
.stButton > button { background: #c1440e !important; color: #fff !important; border: none !important; border-radius: 0 !important; font-family: 'Source Sans 3', sans-serif !important; font-size: 11px !important; font-weight: 700 !important; letter-spacing: 2px !important; text-transform: uppercase !important; padding: 12px 20px !important; }
.stButton > button:hover { background: #a83a0c !important; }

/* ── INPUTS ── */
.stTextInput > div > div > input { background: #fff !important; color: #1a1410 !important; border: 1px solid #d9d0c4 !important; border-radius: 0 !important; font-family: 'Source Sans 3', sans-serif !important; font-size: 14px !important; padding: 12px 16px !important; }
.stTextInput > div > div > input:focus { border-color: #c1440e !important; box-shadow: 0 0 0 3px rgba(193,68,14,0.1) !important; }

/* ── RADIO (email prefs) ── */
.stRadio label { font-family: 'Source Sans 3', sans-serif !important; font-size: 13px !important; color: #3a2e24 !important; }
.stSelectbox label { font-family: 'Source Sans 3', sans-serif !important; }

/* ── CHECKBOXES ── */
.stCheckbox label { font-family: 'Source Sans 3', sans-serif !important; font-size: 11px !important; font-weight: 700 !important; letter-spacing: 1px !important; text-transform: uppercase !important; color: #5a4a3a !important; }

/* ── DIGEST CARDS ── */
.digest-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-bottom: 32px; }
.digest-card { background: #fff; border: 1px solid #e0d8cc; border-top: 3px solid #c1440e; padding: 18px; transition: box-shadow 0.2s; }
.digest-card:hover { box-shadow: 0 4px 16px rgba(26,20,16,0.1); }
.card-source { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #c1440e; text-transform: uppercase; margin-bottom: 8px; }
.card-title { font-family: 'Playfair Display', serif; font-size: 15px; font-weight: 700; color: #1a1410; line-height: 1.4; margin-bottom: 8px; }
.card-title a { color: #1a1410; text-decoration: none; }
.card-title a:hover { color: #c1440e; text-decoration: underline; }
.card-desc { font-size: 12px; color: #6a5a4a; line-height: 1.6; margin-bottom: 10px; }
.card-meta { display: flex; justify-content: space-between; align-items: center; }
.card-date { font-family: 'Source Sans 3', sans-serif; font-size: 10px; color: #c9bfb0; }
.card-bias { font-family: 'Source Sans 3', sans-serif; font-size: 9px; font-weight: 700; padding: 2px 6px; background: #f0ece4; color: #8a7a6a; }

/* ── TRENDING ── */
.trending-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px; }
.trend-chip { background: #fff; border: 1px solid #d9d0c4; padding: 5px 12px; font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 600; color: #3a2e24; display: inline-flex; align-items: center; gap: 6px; text-decoration: none; transition: all 0.15s; }
.trend-chip:hover { background: #c1440e; color: #fff; border-color: #c1440e; }
.trend-num { font-family: 'Playfair Display', serif; font-size: 13px; font-weight: 700; color: #c1440e; }
.trend-chip:hover .trend-num { color: #fff; }

/* ── SAVED TOPICS CHIPS ── */
.saved-chip { background: #1a1410; color: #f5f0e8; padding: 5px 12px; font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; display: inline-block; cursor: pointer; margin: 3px; }

/* ── CAT HEADER ── */
.cat-header { display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #1a1410; padding-bottom: 8px; margin-bottom: 16px; margin-top: 32px; }
.cat-label-text { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: #1a1410; }
.cat-count { font-family: 'Source Sans 3', sans-serif; font-size: 10px; color: #c9bfb0; }

/* ── SECTION HEADERS ── */
.sec { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: #8a7a6a; border-bottom: 2px solid #1a1410; padding-bottom: 8px; margin-bottom: 20px; margin-top: 36px; }
.sec-red { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: #c1440e; border-bottom: 2px solid #c1440e; padding-bottom: 8px; margin-bottom: 20px; margin-top: 36px; }

/* ── DEEP DIVE HEADER ── */
.dd-headline { font-family: 'Playfair Display', serif; font-size: clamp(28px, 4vw, 50px); font-weight: 900; color: #1a1410; line-height: 1.08; letter-spacing: -2px; margin-bottom: 16px; }
.dd-summary { font-family: 'Source Serif 4', serif; font-size: 17px; color: #3a2e24; line-height: 1.8; margin-bottom: 20px; }
.byline { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-top: 1px solid #d9d0c4; border-bottom: 1px solid #d9d0c4; margin-bottom: 32px; }
.byline-text { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 600; color: #8a7a6a; letter-spacing: 1px; text-transform: uppercase; }
.byline-dot { color: #c9bfb0; }

/* ── INSIGHT GRID ── */
.insight-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; margin-bottom: 8px; }
.insight-card { background: #fff; border: 1px solid #e0d8cc; border-left: 4px solid #c1440e; padding: 18px; }
.insight-num { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #c1440e; text-transform: uppercase; margin-bottom: 6px; }
.insight-cat { font-family: 'Source Sans 3', sans-serif; font-size: 9px; font-weight: 700; padding: 2px 7px; background: #f5f0e8; color: #8a7a6a; letter-spacing: 1px; text-transform: uppercase; display: inline-block; margin-bottom: 8px; }
.insight-body { font-size: 14px; color: #1a1410; line-height: 1.7; margin-bottom: 6px; }
.insight-imp { font-size: 12px; font-style: italic; color: #8a7a6a; line-height: 1.6; }
.insight-link { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; color: #c1440e; text-decoration: none; letter-spacing: 1px; text-transform: uppercase; display: inline-block; margin-top: 8px; }
.insight-link:hover { text-decoration: underline; }

/* ── DATA GRID ── */
.data-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 14px; margin-bottom: 8px; }
.data-card { background: #fff; border: 1px solid #e0d8cc; border-top: 3px solid #c1440e; padding: 18px; text-align: center; }
.data-num { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 900; color: #c1440e; line-height: 1; margin-bottom: 6px; }
.data-desc { font-size: 12px; color: #5a4a3a; line-height: 1.5; margin-bottom: 4px; }
.data-src a { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 600; color: #c1440e; text-decoration: none; letter-spacing: 1px; text-transform: uppercase; }
.data-src a:hover { text-decoration: underline; }
.data-src span { font-family: 'Source Sans 3', sans-serif; font-size: 10px; color: #c9bfb0; }

/* ── QUOTES ── */
.quote-block { background: #fff; border: 1px solid #e0d8cc; border-top: 3px solid #c1440e; padding: 20px 24px; margin-bottom: 14px; }
.quote-text { font-family: 'Playfair Display', serif; font-size: 18px; font-style: italic; color: #1a1410; line-height: 1.6; margin-bottom: 10px; }
.quote-footer { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.quote-source { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; color: #8a7a6a; text-transform: uppercase; letter-spacing: 1px; }
.quote-link { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; color: #c1440e; text-decoration: none; letter-spacing: 1px; text-transform: uppercase; }
.quote-link:hover { text-decoration: underline; }
.quote-context { font-size: 13px; font-style: italic; color: #8a7a6a; margin-top: 6px; }

/* ── TIMELINE ── */
.tl { display: flex; gap: 16px; padding-bottom: 20px; }
.tl-spine { display: flex; flex-direction: column; align-items: center; }
.tl-dot { width: 9px; height: 9px; background: #c1440e; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.tl-line { width: 1px; background: #d9d0c4; flex: 1; min-height: 16px; margin: 4px 0; }
.tl-date { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #c1440e; text-transform: uppercase; margin-bottom: 4px; }
.tl-event { font-size: 14px; color: #1a1410; line-height: 1.65; margin-bottom: 3px; }
.tl-sig { font-size: 12px; font-style: italic; color: #8a7a6a; line-height: 1.5; }

/* ── SOURCE GRID ── */
.source-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.source-card { background: #fff; border: 1px solid #e0d8cc; padding: 16px; }
.source-name { font-family: 'Playfair Display', serif; font-size: 16px; font-weight: 700; color: #1a1410; margin-bottom: 8px; }
.source-tags { display: flex; gap: 5px; margin-bottom: 8px; flex-wrap: wrap; }
.stag { font-family: 'Source Sans 3', sans-serif; font-size: 9px; font-weight: 700; padding: 2px 7px; text-transform: uppercase; letter-spacing: 0.5px; }
.stag-pos { background: #e8f5ee; color: #2a7a4a; }
.stag-neg { background: #fceee8; color: #c1440e; }
.stag-neu { background: #f0ece4; color: #8a7a6a; }
.stag-mix { background: #fdf3e0; color: #9a6a10; }
.source-cred-bar { height: 3px; background: #e0d8cc; margin-bottom: 8px; }
.source-cred-fill { height: 100%; background: #c1440e; }
.source-cred-label { font-family: 'Source Sans 3', sans-serif; font-size: 10px; color: #c9bfb0; margin-bottom: 6px; }
.source-framing { font-size: 13px; color: #3a2e24; line-height: 1.65; }
.source-angle { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; color: #c9bfb0; text-transform: uppercase; margin-top: 6px; }

/* ── ASSESS ── */
.assess-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.assess-card { background: #fff; border: 1px solid #e0d8cc; padding: 20px; }
.assess-tag { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #c1440e; text-transform: uppercase; margin-bottom: 10px; }
.assess-body { font-size: 14px; color: #3a2e24; line-height: 1.75; }

/* ── SENTIMENT ── */
.sentiment-wrap { background: #fff; border: 1px solid #e0d8cc; padding: 18px 20px; }
.sentiment-bar { display: flex; height: 18px; overflow: hidden; margin: 8px 0; }
.s-pos { background: #2a7a4a; }
.s-neu { background: #c9bfb0; }
.s-neg { background: #c1440e; }
.sentiment-legend { display: flex; gap: 16px; margin-top: 6px; }
.s-legend-item { display: flex; align-items: center; gap: 5px; font-family: 'Source Sans 3', sans-serif; font-size: 11px; color: #8a7a6a; }
.s-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

/* ── ENTITIES ── */
.entity-chip { background: #1a1410; color: #f5f0e8; font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; padding: 4px 10px; letter-spacing: 0.5px; display: inline-block; margin: 3px; }

/* ── ARTICLE ROWS ── */
.article-row { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid #e0d8cc; }
.a-src { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #c1440e; text-transform: uppercase; min-width: 100px; padding-top: 2px; }
.a-date { font-family: 'Source Sans 3', sans-serif; font-size: 10px; color: #c9bfb0; min-width: 80px; padding-top: 2px; }
.a-title a { font-size: 13px; color: #3a2e24; text-decoration: none; font-weight: 600; }
.a-title a:hover { color: #c1440e; text-decoration: underline; }

/* ── EMAIL PREFS ── */
.pref-box { background: #fff; border: 1px solid #e0d8cc; border-top: 3px solid #c1440e; padding: 20px 24px; margin-top: 16px; }
</style>
""", unsafe_allow_html=True)

now = datetime.now()
today = now.strftime("%B %d, %Y").upper()

# ── HEADER (logo centré) ─────────────────────────────────────────────────────
st.markdown(f"""
<div class="site-header">
    <div class="site-left">
        <div class="site-date">{today}</div>
    </div>
    <div class="site-logo-wrap">
        <div class="site-logo">The <em>Brief</em></div>
        <div class="site-tagline">AI-Powered News Intelligence</div>
    </div>
    <div style="min-width:140px;"></div>
</div>
<div class="red-stripe"></div>
""", unsafe_allow_html=True)

# ── MARKET TICKER ────────────────────────────────────────────────────────────
stocks = fetch_stock_data()
if stocks:
    ticker_html = '<div class="ticker-bar">'
    for s in stocks:
        sign = "▲" if s["up"] else "▼"
        cls = "ticker-up" if s["up"] else "ticker-down"
        pct = f"{s['change_pct']:+.2f}%"
        price_fmt = f"{s['price']:,.2f}" if s["price"] < 10000 else f"{s['price']:,.0f}"
        ticker_html += f'<div class="ticker-item"><span class="ticker-name">{s["name"]}</span><span class="ticker-price">{price_fmt}</span><span class="{cls}">{sign} {pct}</span></div>'
    ticker_html += '</div>'
    st.markdown(ticker_html, unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📰 Daily Digest", "🔍 Deep Dive", "✉️ Email Preferences"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — DAILY DIGEST
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    P = "padding: 24px 48px;"

    # ── Category filter ──
    st.markdown(f'<div style="{P} padding-bottom:8px;">', unsafe_allow_html=True)
    all_cats = list(CATEGORY_LABELS.keys())
    col_label, *col_cats = st.columns([1] + [2] * len(all_cats))
    with col_label:
        st.markdown('<div style="padding-top:10px; font-family:\'Source Sans 3\',sans-serif; font-size:10px; font-weight:700; letter-spacing:1px; color:#8a7a6a; text-transform:uppercase;">Show:</div>', unsafe_allow_html=True)
    selected_cats = []
    for i, cat in enumerate(all_cats):
        with col_cats[i]:
            if st.checkbox(CATEGORY_LABELS[cat], value=True, key=f"cat_{cat}"):
                selected_cats.append(cat)
    st.markdown('</div><div style="height:1px;background:#d9d0c4;margin:0 48px;"></div>', unsafe_allow_html=True)

    # ── Load data ──
    with st.spinner("Loading today's news..."):
        digest = fetch_full_digest()
        trending = fetch_trending_topics()

    # ── Saved custom topics (persistent) ──
    saved_topics = load_saved_topics()
    if saved_topics:
        st.markdown(f'<div style="{P} padding-bottom:0; padding-top:24px;">', unsafe_allow_html=True)
        st.markdown('<div class="sec-red" style="margin-top:0;">📌 Your Saved Topics</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        cols = st.columns(len(saved_topics) + 1)
        for i, t in enumerate(saved_topics):
            with cols[i]:
                st.markdown(f'<div style="font-family:\'Source Sans 3\',sans-serif; font-size:12px; font-weight:700; background:#1a1410; color:#f5f0e8; padding:8px 14px; text-align:center; margin-bottom:4px;">{t}</div>', unsafe_allow_html=True)
                if st.button(f"✕ Remove", key=f"remove_{i}"):
                    saved_topics.pop(i)
                    save_topics_to_file(saved_topics)
                    st.rerun()
        st.markdown(f'<div style="{P} padding-top:4px; padding-bottom:0;"><div style="font-family:\'Source Sans 3\',sans-serif; font-size:11px; color:#8a7a6a; font-style:italic; margin-bottom:8px;">Switch to Deep Dive to analyze any of these topics.</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="height:1px; background:#d9d0c4; margin:0 48px 0;"></div>', unsafe_allow_html=True)

    # ── Trending ──
    st.markdown(f'<div style="{P} padding-bottom:0;">', unsafe_allow_html=True)
    st.markdown('<div class="sec-red" style="margin-top:16px;">🔥 Trending Now</div>', unsafe_allow_html=True)
    trend_html = '<div class="trending-row">'
    for i, t in enumerate(trending[:12], 1):
        url = t.get("url", "#")
        title = t.get("title", "")[:55] + ("…" if len(t.get("title","")) > 55 else "")
        src = t.get("source", "")
        trend_html += f'<a href="{url}" target="_blank" class="trend-chip"><span class="trend-num">{i:02d}</span>{title} <span style="color:#c9bfb0; font-size:9px; margin-left:4px;">{src}</span></a>'
    trend_html += '</div>'
    st.markdown(trend_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── News grid by category ──
    st.markdown(f'<div style="{P} padding-top:0;">', unsafe_allow_html=True)
    for category in all_cats:
        if category not in selected_cats:
            continue
        articles = digest.get(category, [])
        if not articles:
            continue
        label = CATEGORY_LABELS.get(category, category.title())
        st.markdown(f'<div class="cat-header"><span class="cat-label-text">{label}</span><span class="cat-count">{len(articles)} stories</span></div>', unsafe_allow_html=True)
        cards_html = '<div class="digest-grid">'
        for a in articles:
            src = a.get("source", "")
            title = a.get("title", "")
            url = a.get("url", "")
            desc = a.get("description", "")[:120]
            date = a.get("publishedAt", "")
            bias = a.get("bias", "")
            linked = f'<a href="{url}" target="_blank">{title}</a>' if url else title
            cards_html += f'<div class="digest-card"><div class="card-source">{src}</div><div class="card-title">{linked}</div><div class="card-desc">{desc}{"…" if desc else ""}</div><div class="card-meta"><span class="card-date">{date}</span><span class="card-bias">{bias}</span></div></div>'
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — DEEP DIVE
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    P = "padding: 0 48px;"

    st.markdown('<div style="background:#fff; border-bottom:1px solid #d9d0c4; padding:16px 48px; display:flex; align-items:center; gap:12px;">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        topic = st.text_input("", placeholder="e.g. OpenAI GPT-5, Ukraine ceasefire, Fed interest rates...", label_visibility="collapsed", key="topic_input")
    with col2:
        analyze_btn = st.button("Analyze →", use_container_width=True, key="analyze_btn")
    with col3:
        save_btn = st.button("+ Save Topic", use_container_width=True, key="save_btn")
    st.markdown('</div>', unsafe_allow_html=True)

    # Save topic to digest page (persistent)
    if save_btn and topic:
        saved_topics = load_saved_topics()
        if topic not in saved_topics:
            saved_topics.append(topic)
            save_topics_to_file(saved_topics)
            st.success(f"✅ '{topic}' pinned to your Daily Digest!")
        else:
            st.info("Already saved.")

    if not analyze_btn or not topic:
        st.markdown("""
        <div style="max-width:580px; margin:72px auto; text-align:center; padding:0 40px;">
            <div style="font-family:'Playfair Display',serif; font-size:42px; font-weight:900; color:#1a1410; line-height:1.1; letter-spacing:-2px; margin-bottom:16px;">Deep Dive.<br>Any topic.</div>
            <div style="font-family:'Source Serif 4',serif; font-size:16px; color:#8a7a6a; font-style:italic; line-height:1.8;">Enter a specific topic to receive a full intelligence brief with insights, data, source analysis, and bias assessment.</div>
        </div>""", unsafe_allow_html=True)
    else:
        with st.spinner(f"Finding articles on '{topic}'..."):
            newsapi_articles = fetch_newsapi(topic)
            rss_articles = fetch_rss(topic.split())
            all_articles = enrich_with_metadata(newsapi_articles) + rss_articles
            seen = set()
            unique = []
            for a in all_articles:
                if a["title"] not in seen:
                    seen.add(a["title"])
                    unique.append(a)
            all_articles = unique[:12]

        if not all_articles:
            st.markdown('<div style="padding:48px; text-align:center; color:#8a7a6a; font-style:italic; font-size:16px;">No articles found for this topic. Try more specific keywords.</div>', unsafe_allow_html=True)
            st.stop()

        with st.spinner("Composing your intelligence brief..."):
            try:
                analysis = analyze_articles(all_articles)
            except Exception as e:
                st.error(f"Analysis error: {e}")
                st.stop()

        source_count = len(set(a['source'] for a in all_articles))

        # ── BRIEF HEADER ────────────────────────────────────────
        st.markdown(f"""
        <div style="padding:32px 48px 0;">
            <div style="font-family:'Source Sans 3',sans-serif; font-size:10px; font-weight:700; letter-spacing:3px; color:#c1440e; text-transform:uppercase; margin-bottom:10px;">
                {today} &nbsp;·&nbsp; {source_count} Sources &nbsp;·&nbsp; {len(all_articles)} Articles
            </div>
            <div class="dd-headline">{analysis.get('headline', topic.title())}</div>
            <div class="dd-summary">{analysis.get('summary', '')}</div>
            <div class="byline">
                <span class="byline-text">AI Analysis</span><span class="byline-dot">·</span>
                <span class="byline-text">The Brief</span><span class="byline-dot">·</span>
                <span class="byline-text">{today}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── SENTIMENT + ENTITIES ─────────────────────────────────
        sent = analysis.get("sentiment_breakdown", {"positive": 33, "neutral": 34, "negative": 33})
        entities = analysis.get("top_entities", [])
        col_s, col_e = st.columns(2)

        with col_s:
            st.markdown('<div style="padding:0 12px 0 48px;">', unsafe_allow_html=True)
            st.markdown('<div class="sec-red">Media Sentiment</div>', unsafe_allow_html=True)
            pos, neu, neg = sent.get("positive",33), sent.get("neutral",34), sent.get("negative",33)
            st.markdown(f"""
            <div class="sentiment-wrap">
                <div class="sentiment-bar">
                    <div class="s-pos" style="width:{pos}%;"></div>
                    <div class="s-neu" style="width:{neu}%;"></div>
                    <div class="s-neg" style="width:{neg}%;"></div>
                </div>
                <div class="sentiment-legend">
                    <div class="s-legend-item"><span class="s-dot" style="background:#2a7a4a;"></span> Positive {pos}%</div>
                    <div class="s-legend-item"><span class="s-dot" style="background:#c9bfb0;"></span> Neutral {neu}%</div>
                    <div class="s-legend-item"><span class="s-dot" style="background:#c1440e;"></span> Negative {neg}%</div>
                </div>
            </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_e:
            if entities:
                st.markdown('<div style="padding:0 48px 0 12px;">', unsafe_allow_html=True)
                st.markdown('<div class="sec-red">Key Entities</div>', unsafe_allow_html=True)
                chips = "".join(f'<span class="entity-chip">{e}</span>' for e in entities)
                st.markdown(f'<div style="margin-bottom:8px;">{chips}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # ── DATA POINTS ──────────────────────────────────────────
        data_points = analysis.get("data_points", [])
        if data_points:
            st.markdown(f'<div style="{P}">', unsafe_allow_html=True)
            st.markdown('<div class="sec-red">By The Numbers</div>', unsafe_allow_html=True)
            grid = '<div class="data-grid">'
            for dp in data_points[:6]:
                dp_url = dp.get("url", "")
                src_html = f'<a href="{dp_url}" target="_blank">{dp.get("source","")}</a>' if dp_url else f'<span>{dp.get("source","")}</span>'
                grid += f'<div class="data-card"><div class="data-num">{dp.get("value","")}</div><div class="data-desc">{dp.get("context","")}</div><div class="data-src">{src_html}</div></div>'
            grid += '</div>'
            st.markdown(grid + '</div>', unsafe_allow_html=True)

        # ── KEY FINDINGS (with links) ────────────────────────────
        insights = analysis.get("key_insights", [])
        if insights:
            st.markdown(f'<div style="{P}">', unsafe_allow_html=True)
            st.markdown('<div class="sec">Key Findings</div>', unsafe_allow_html=True)
            # Match each insight to a source article URL
            grid = '<div class="insight-grid">'
            for i, item in enumerate(insights, 1):
                cat_label = item.get("category", "")
                # Try to find a related article URL
                insight_text = item.get("insight", "").lower()
                related_url = ""
                for a in all_articles:
                    if any(w in insight_text for w in a["title"].lower().split() if len(w) > 4):
                        related_url = a.get("url", "")
                        break
                link_html = f'<a class="insight-link" href="{related_url}" target="_blank">Read source →</a>' if related_url else ''
                grid += f"""<div class="insight-card">
                    <div class="insight-num">Finding {i:02d}</div>
                    {'<div class="insight-cat">' + cat_label + '</div>' if cat_label else ''}
                    <div class="insight-body">{item.get("insight","")}</div>
                    <div class="insight-imp">{item.get("importance","")}</div>
                    {link_html}
                </div>"""
            grid += '</div>'
            st.markdown(grid + '</div>', unsafe_allow_html=True)

        # ── NOTABLE QUOTES ───────────────────────────────────────
        quotes = analysis.get("quotes", [])
        if quotes:
            st.markdown(f'<div style="{P}">', unsafe_allow_html=True)
            st.markdown('<div class="sec">Notable Claims</div>', unsafe_allow_html=True)
            for q in quotes[:3]:
                qurl = q.get('url', '')
                link = f'<a class="quote-link" href="{qurl}" target="_blank">Read source →</a>' if qurl else ''
                st.markdown(f"""<div class="quote-block">
                    <div class="quote-text">"{q.get("text","")}"</div>
                    <div class="quote-footer">
                        <span class="quote-source">{q.get("source","")}</span>
                        {link}
                    </div>
                    <div class="quote-context">{q.get("context","")}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── TIMELINE ─────────────────────────────────────────────
        timeline = analysis.get("timeline", [])
        if timeline:
            st.markdown(f'<div style="{P}">', unsafe_allow_html=True)
            st.markdown('<div class="sec">Chronology</div>', unsafe_allow_html=True)
            for item in timeline:
                st.markdown(f"""<div class="tl">
                    <div class="tl-spine"><div class="tl-dot"></div><div class="tl-line"></div></div>
                    <div><div class="tl-date">{item.get("date","")}</div>
                    <div class="tl-event">{item.get("event","")}</div>
                    <div class="tl-sig">{item.get("significance","")}</div></div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── EDITORIAL ASSESSMENT ─────────────────────────────────
        st.markdown(f'<div style="{P}">', unsafe_allow_html=True)
        st.markdown('<div class="sec">Editorial Assessment</div>', unsafe_allow_html=True)
        st.markdown('<div class="assess-grid">', unsafe_allow_html=True)
        for label, key in [("Where Sources Agree", "consensus"), ("Where They Diverge", "divergence"), ("Missing Perspectives", "missing_perspectives")]:
            st.markdown(f'<div class="assess-card"><div class="assess-tag">{label}</div><div class="assess-body">{analysis.get(key,"")}</div></div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        # ── SOURCE BREAKDOWN ─────────────────────────────────────
        sources = analysis.get("source_analysis", [])
        if sources:
            st.markdown(f'<div style="{P}">', unsafe_allow_html=True)
            st.markdown('<div class="sec">Source Breakdown</div>', unsafe_allow_html=True)
            st.markdown('<div class="source-grid">', unsafe_allow_html=True)
            for s in sources:
                sentiment = s.get("sentiment", "Neutral").lower()
                bmap = {"positive": "stag-pos", "negative": "stag-neg", "neutral": "stag-neu", "mixed": "stag-mix"}
                bcls = bmap.get(sentiment, "stag-neu")
                cred = s.get("credibility", 5)
                st.markdown(f"""<div class="source-card">
                    <div class="source-name">{s.get("source","")}</div>
                    <div class="source-tags">
                        <span class="stag {bcls}">{s.get("sentiment","")}</span>
                        <span class="stag stag-neu">{s.get("bias","")}</span>
                    </div>
                    <div class="source-cred-label">Credibility: {cred}/10</div>
                    <div class="source-cred-bar"><div class="source-cred-fill" style="width:{cred*10}%;"></div></div>
                    <div class="source-framing">{s.get("framing","")}</div>
                    <div class="source-angle">{s.get("key_angle","")}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            bias_summary = analysis.get("bias_summary", "")
            if bias_summary:
                st.markdown(f'<div class="assess-card" style="margin-top:14px;"><div class="assess-tag">Bias Summary</div><div class="assess-body">{bias_summary}</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── ALL ARTICLES ─────────────────────────────────────────
        with st.expander(f"📄 All {len(all_articles)} Articles Reviewed"):
            rows = ""
            for a in all_articles:
                aurl = a.get("url", "")
                linked = f'<a href="{aurl}" target="_blank">{a["title"]}</a>' if aurl else a["title"]
                rows += f'<div class="article-row"><div class="a-src">{a["source"]}</div><div class="a-date">{a.get("publishedAt","")}</div><div class="a-title">{linked}</div></div>'
            st.markdown(f'<div style="padding:8px 0;">{rows}</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:48px;"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — EMAIL PREFERENCES (compact)
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div style="max-width:480px; margin:32px auto; padding:0 32px;">', unsafe_allow_html=True)

    st.markdown('<div style="font-family:\'Playfair Display\',serif; font-size:24px; font-weight:900; color:#1a1410; margin-bottom:4px;">Email Notifications</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Source Serif 4\',serif; font-size:14px; color:#8a7a6a; font-style:italic; margin-bottom:20px; line-height:1.6;">Configure your daily intelligence brief delivery.</div>', unsafe_allow_html=True)

    st.markdown('<div class="sec" style="margin-top:0; font-size:10px;">Schedule</div>', unsafe_allow_html=True)
    sched_choice = st.radio("Delivery", ["Morning only (8:00 AM)", "Evening only (7:00 PM)", "Both (8:00 AM + 7:00 PM)"], index=2, label_visibility="collapsed")
    schedule_map = {"Morning only (8:00 AM)": "morning", "Evening only (7:00 PM)": "evening", "Both (8:00 AM + 7:00 PM)": "both"}
    chosen = schedule_map[sched_choice]

    st.markdown('<div class="sec" style="font-size:10px;">Test Email</div>', unsafe_allow_html=True)
    tc1, tc2 = st.columns([2, 1])
    with tc1:
        test_period = st.selectbox("Type", ["Morning Brief", "Evening Brief"], label_visibility="collapsed")
    with tc2:
        if st.button("Send Test →", key="test_email"):
            period = "morning" if "Morning" in test_period else "evening"
            with st.spinner("Sending..."):
                try:
                    from notifier import send_digest_email
                    result = send_digest_email(period)
                    if result:
                        st.success("✅ Sent!")
                    else:
                        st.error("❌ Check .env")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown(f"""
    <div class="pref-box">
        <div style="font-family:'Source Sans 3',sans-serif; font-size:10px; font-weight:700; letter-spacing:2px; color:#c1440e; text-transform:uppercase; margin-bottom:10px;">Apply Changes</div>
        <div style="font-size:13px; color:#5a4a3a; line-height:1.8;">
            Add to <code style="background:#f5f0e8; padding:1px 5px;">.env</code>:<br>
            <code style="background:#1a1410; color:#f5f0e8; padding:6px 12px; display:inline-block; margin-top:6px; font-size:12px;">EMAIL_SCHEDULE={chosen}</code><br>
            <span style="font-size:12px; color:#8a7a6a; margin-top:6px; display:inline-block;">Then restart scheduler.py</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
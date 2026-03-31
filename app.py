import streamlit as st
from collector import fetch_newsapi, fetch_rss, enrich_with_metadata
from analyzer import analyze_articles
from digest import fetch_full_digest, CATEGORY_LABELS
from mailer import add_subscriber, remove_subscriber, load_subscribers, send_brief_to_all, send_email, build_email_html
from datetime import datetime

import yfinance as yf

@st.cache_data(ttl=300)
def get_ticker_data():
    symbols = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DOW JONES": "^DJI",
        "BITCOIN": "BTC-USD",
        "GOLD": "GC=F",
        "EUR/USD": "EURUSD=X",
    }
    items = []
    for name, symbol in symbols.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                prev = hist["Close"].iloc[-2]
                curr = hist["Close"].iloc[-1]
                change = ((curr - prev) / prev) * 100
                arrow = "▲" if change >= 0 else "▼"
                cls = "up" if change >= 0 else "down"
                price = f"{curr:,.2f}"
                items.append(f'<span class="ticker-item"><b>{name}</b> {price} <span class="{cls}">{arrow} {abs(change):.2f}%</span></span>')
        except:
            pass
    return items * 2
    
st.set_page_config(page_title="The Brief — News Intelligence", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400;1,700&family=Source+Sans+3:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { background: #f5f0e8 !important; color: #1a1410 !important; font-family: 'Source Serif 4', serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.site-header { background: #1a1410; padding: 28px 40px 24px; text-align: center; position: relative; }
.site-logo { font-family: 'Playfair Display', serif; font-size: 42px; font-weight: 900; color: #f5f0e8; letter-spacing: -1px; line-height: 1; margin-bottom: 6px; }
.site-logo em { color: #c1440e; font-style: normal; }
.site-tagline { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 400; letter-spacing: 3px; color: #6b5d50; text-transform: uppercase; }
.site-meta-bar { position: absolute; right: 40px; top: 50%; transform: translateY(-50%); font-family: 'Source Sans 3', sans-serif; font-size: 11px; color: #4a3d32; text-align: right; line-height: 1.6; }
.red-stripe { background: #c1440e; height: 4px; }
.ticker { background: #1a1410; padding: 8px 0; overflow: hidden; white-space: nowrap; }
.ticker-inner { display: inline-flex; gap: 48px; animation: ticker 30s linear infinite; }
.ticker-item { font-family: 'Source Sans 3', sans-serif; font-size: 12px; color: #f5f0e8; }
.ticker-item b { color: #c9bfb0; font-weight: 600; margin-right: 6px; }
.ticker-item .up { color: #4caf50; }
.ticker-item .down { color: #c1440e; }
@keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
.nav-tabs { display: flex; background: #f5f0e8; border-bottom: 1px solid #d9d0c4; padding: 0 40px; }
.nav-tab { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; padding: 14px 20px; cursor: pointer; border-bottom: 3px solid transparent; color: #8a7a6a; margin-bottom: -1px; }
.nav-tab.active { color: #1a1410; border-bottom-color: #c1440e; }
.article { max-width: 780px; margin: 0 auto; padding: 64px 40px 100px; }
.kicker { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 3px; color: #c1440e; text-transform: uppercase; margin-bottom: 16px; display: flex; gap: 16px; flex-wrap: wrap; }
.kicker-sep { color: #c9bfb0; font-weight: 300; }
.headline { font-family: 'Playfair Display', serif; font-size: clamp(38px, 6vw, 68px); font-weight: 900; color: #1a1410; line-height: 1.06; letter-spacing: -2px; margin-bottom: 28px; text-align: center; }
.summary { font-family: 'Source Serif 4', serif; font-size: 20px; color: #3a2e24; line-height: 1.9; margin-bottom: 40px; }
.byline { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 20px 0; border-top: 1px solid #d9d0c4; border-bottom: 1px solid #d9d0c4; margin-bottom: 56px; }
.byline-text { font-family: 'Source Sans 3', sans-serif; font-size: 12px; font-weight: 600; color: #8a7a6a; letter-spacing: 1px; text-transform: uppercase; }
.byline-dot { color: #c9bfb0; }
.sec { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: #8a7a6a; border-bottom: 2px solid #1a1410; padding-bottom: 10px; margin-bottom: 32px; margin-top: 56px; }
.sec-red { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: #c1440e; border-bottom: 2px solid #c1440e; padding-bottom: 10px; margin-bottom: 32px; margin-top: 56px; }
.rule { border: none; border-top: 1px solid #d9d0c4; margin: 48px 0; }
.data-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 8px; }
.data-card { background: #fff; border: 1px solid #e0d8cc; border-top: 3px solid #c1440e; padding: 20px; text-align: center; }
.data-num { font-family: 'Playfair Display', serif; font-size: 44px; font-weight: 900; color: #c1440e; line-height: 1; margin-bottom: 10px; }
.data-desc { font-size: 13px; color: #5a4a3a; line-height: 1.5; margin-bottom: 4px; }
.data-src { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: 1px; color: #c9bfb0; text-transform: uppercase; }
.finding { border-left: 4px solid #c1440e; padding: 4px 0 4px 24px; margin-bottom: 40px; }
.finding-n { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #c1440e; text-transform: uppercase; margin-bottom: 12px; }
.finding-body { font-size: 17px; color: #1a1410; line-height: 1.85; margin-bottom: 10px; }
.finding-imp { font-family: 'Source Serif 4', serif; font-size: 14px; font-style: italic; color: #8a7a6a; line-height: 1.6; }
.pq { border-top: 3px solid #c1440e; border-bottom: 1px solid #d9d0c4; padding: 32px 0; margin: 40px 0; text-align: center; }
.pq-tag { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #c1440e; text-transform: uppercase; margin-bottom: 16px; }
.pq-text { font-family: 'Playfair Display', serif; font-size: 24px; font-style: italic; color: #3a2e24; line-height: 1.6; margin-bottom: 16px; padding: 0 24px; }
.pq-source { font-family: 'Source Sans 3', sans-serif; font-size: 12px; font-weight: 600; color: #8a7a6a; letter-spacing: 1px; text-transform: uppercase; }
.pq-context { font-family: 'Source Serif 4', serif; font-size: 14px; color: #8a7a6a; font-style: italic; margin-top: 10px; line-height: 1.6; }
.tl { display: flex; gap: 20px; padding-bottom: 32px; }
.tl-spine { display: flex; flex-direction: column; align-items: center; }
.tl-dot { width: 10px; height: 10px; background: #c1440e; border-radius: 50%; flex-shrink: 0; margin-top: 6px; }
.tl-line { width: 1px; background: #d9d0c4; flex: 1; min-height: 24px; margin: 4px 0; }
.tl-date { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #c1440e; text-transform: uppercase; margin-bottom: 8px; }
.tl-event { font-size: 16px; color: #1a1410; line-height: 1.75; margin-bottom: 6px; }
.tl-sig { font-family: 'Source Serif 4', serif; font-size: 14px; font-style: italic; color: #8a7a6a; line-height: 1.6; }
.src-prose { margin-bottom: 36px; padding-bottom: 36px; border-bottom: 1px solid #e0d8cc; }
.src-prose-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.src-prose-name { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #1a1410; }
.src-tags { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.stag { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; padding: 3px 9px; border-radius: 2px; text-transform: uppercase; letter-spacing: 0.5px; display: inline-block; }
.stag-pos { background: #e8f5ee; color: #2a7a4a; }
.stag-neg { background: #fceee8; color: #c1440e; }
.stag-neu { background: #f0ece4; color: #8a7a6a; }
.stag-mix { background: #fdf3e0; color: #9a6a10; }
.src-cred { font-family: 'Source Sans 3', sans-serif; font-size: 11px; color: #8a7a6a; margin-bottom: 10px; }
.src-cred b { color: #c1440e; }
.src-prose-text { font-size: 16px; color: #3a2e24; line-height: 1.85; margin-bottom: 8px; }
.src-prose-angle { font-family: 'Source Sans 3', sans-serif; font-size: 12px; font-weight: 600; color: #c9bfb0; text-transform: uppercase; letter-spacing: 0.5px; }
.assess { margin-bottom: 36px; }
.assess-tag { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 2px; color: #c1440e; text-transform: uppercase; margin-bottom: 12px; }
.assess-body { font-size: 17px; color: #3a2e24; line-height: 1.85; }
.dispatch { display: flex; gap: 16px; padding: 12px 0; border-bottom: 1px solid #e0d8cc; align-items: flex-start; }
.d-src { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #c1440e; text-transform: uppercase; min-width: 120px; padding-top: 2px; }
.d-date { font-family: 'Source Sans 3', sans-serif; font-size: 11px; color: #c9bfb0; min-width: 90px; padding-top: 2px; }
.d-title a { font-size: 14px; color: #5a4a3a; text-decoration: none; line-height: 1.5; }
.d-title a:hover { color: #1a1410; text-decoration: underline; }
.digest-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; padding: 32px 40px; }
.digest-card { background: #fff; border: 1px solid #e0d8cc; border-top: 3px solid #c1440e; padding: 24px; }
.dc-source { font-family: 'Source Sans 3', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #c1440e; text-transform: uppercase; margin-bottom: 10px; }
.dc-title { font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #1a1410; line-height: 1.3; margin-bottom: 10px; }
.dc-title a { color: #1a1410; text-decoration: none; }
.dc-title a:hover { color: #c1440e; }
.dc-desc { font-size: 14px; color: #5a4a3a; line-height: 1.6; margin-bottom: 12px; }
.dc-date { font-family: 'Source Sans 3', sans-serif; font-size: 11px; color: #c9bfb0; }
.cat-header { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: #8a7a6a; border-bottom: 2px solid #1a1410; padding: 0 40px 10px; margin: 40px 40px 0; }
.trending { padding: 24px 40px; border-bottom: 1px solid #d9d0c4; }
.trending-label { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 2px; color: #c1440e; text-transform: uppercase; margin-bottom: 16px; }
.trending-items { display: flex; gap: 16px; flex-wrap: wrap; }
.trending-item { font-size: 14px; color: #3a2e24; padding: 8px 16px; background: #fff; border: 1px solid #e0d8cc; }
.trending-item span { color: #c1440e; font-weight: 700; margin-right: 8px; font-family: 'Source Sans 3', sans-serif; font-size: 11px; }
.sub-box { max-width: 560px; margin: 0 auto; padding: 64px 40px; }
.sub-title { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 900; color: #1a1410; margin-bottom: 12px; }
.sub-desc { font-family: 'Source Serif 4', serif; font-size: 17px; color: #5a4a3a; line-height: 1.8; margin-bottom: 40px; }
.sub-label { font-family: 'Source Sans 3', sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 2px; color: #8a7a6a; text-transform: uppercase; margin-bottom: 8px; margin-top: 24px; }
.sub-list { margin-top: 32px; }
.sub-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #e0d8cc; font-size: 14px; color: #3a2e24; }
.stTextInput > div > div > input { background: #fff !important; color: #1a1410 !important; border: 1px solid #d9d0c4 !important; border-radius: 3px !important; font-family: 'Source Sans 3', sans-serif !important; font-size: 15px !important; padding: 12px 16px !important; }
.stTextInput > div > div > input:focus { border-color: #c1440e !important; box-shadow: 0 0 0 3px rgba(193,68,14,0.1) !important; }
.stButton > button { background: #c1440e !important; color: #fff !important; border: none !important; border-radius: 3px !important; font-family: 'Source Sans 3', sans-serif !important; font-size: 13px !important; font-weight: 700 !important; letter-spacing: 1px !important; text-transform: uppercase !important; padding: 12px 24px !important; }
.stButton > button:hover { background: #a83a0c !important; }
.stRadio > div { gap: 12px !important; }
.stRadio label { font-family: 'Source Sans 3', sans-serif !important; font-size: 14px !important; color: #3a2e24 !important; }
.stCheckbox label { font-family: 'Source Sans 3', sans-serif !important; font-size: 14px !important; color: #3a2e24 !important; }
div[data-testid="stSpinner"] p { color: #8a7a6a !important; font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

now = datetime.now()
today = now.strftime("%B %d, %Y").upper()

st.markdown(f"""
<div class="site-header">
    <div class="site-logo">The <em>Brief</em></div>
    <div class="site-tagline">AI-Powered News Intelligence</div>
    <div class="site-meta-bar">{today}</div>
</div>
<div class="red-stripe"></div>
</div>
""", unsafe_allow_html=True)

ticker_items = get_ticker_data()
ticker_html = '<div class="ticker"><div class="ticker-inner">' + "".join(ticker_items) + '</div></div>'
st.markdown(ticker_html, unsafe_allow_html=True)

unsafe_allow_html=True)

if "tab" not in st.session_state:
    st.session_state.tab = "digest"

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("📰 Daily Digest", use_container_width=True):
        st.session_state.tab = "digest"
with col2:
    if st.button("🔍 Deep Dive", use_container_width=True):
        st.session_state.tab = "deepdive"
with col3:
    if st.button("✉️ Subscribe", use_container_width=True):
        st.session_state.tab = "subscribe"

tab = st.session_state.tab

if tab == "digest":
    with st.spinner("Loading today's digest..."):
        digest = fetch_full_digest()

    all_top = []
    for cat, articles in digest.items():
        all_top.extend(articles[:2])

    if all_top:
        st.markdown('<div class="trending"><div class="trending-label">🔥 Trending Now</div><div class="trending-items">', unsafe_allow_html=True)
        items = ""
        for i, a in enumerate(all_top[:6], 1):
            url = a.get("url", "")
            title = a.get("title", "")
            source = a.get("source", "")
            items += f'<div class="trending-item"><span>0{i}</span><a href="{url}" target="_blank" style="color:#3a2e24;text-decoration:none;">{title[:60]}...</a> <span style="color:#c9bfb0;font-size:11px;">{source}</span></div>'
        st.markdown(items + '</div></div>', unsafe_allow_html=True)

    cat_labels = {"world": "🌍 Top World News", "tech": "💻 Technology", "business": "📈 Business & Economy", "politics": "🏛 Politics"}
    for cat, articles in digest.items():
        if not articles:
            continue
        label = cat_labels.get(cat, cat.title())
        count = len(articles)
        st.markdown(f'<div class="cat-header">{label} <span style="color:#c9bfb0;font-weight:400;font-size:10px;margin-left:8px;">{count} stories</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="digest-grid">', unsafe_allow_html=True)
        cards = ""
        for a in articles:
            title = a.get("title", "")
            source = a.get("source", "")
            url = a.get("url", "")
            desc = a.get("description", "")[:180]
            date = a.get("publishedAt", "")
            cards += f'<div class="digest-card"><div class="dc-source">{source}</div><div class="dc-title"><a href="{url}" target="_blank">{title}</a></div><div class="dc-desc">{desc}...</div><div class="dc-date">{date}</div></div>'
        st.markdown(cards + '</div>', unsafe_allow_html=True)

elif tab == "deepdive":
    col1, col2 = st.columns([6, 1])
    with col1:
        topic = st.text_input("", placeholder="e.g. artificial intelligence, Ukraine, climate policy...", label_visibility="collapsed")
    with col2:
        analyze_btn = st.button("Analyze →", use_container_width=True)

    st.markdown('<div style="border-bottom:1px solid #d9d0c4"></div>', unsafe_allow_html=True)

    if analyze_btn and topic:
        with st.spinner("Gathering articles from global sources..."):
            topic_keywords = topic.split()
            newsapi_articles = fetch_newsapi(topic)
            rss_articles = fetch_rss(topic_keywords)
            all_articles = enrich_with_metadata(newsapi_articles) + rss_articles
            seen = set()
            unique = []
            for a in all_articles:
                if a["title"] not in seen:
                    seen.add(a["title"])
                    unique.append(a)
            all_articles = unique[:20]

        with st.spinner("Composing your intelligence brief..."):
            try:
                analysis = analyze_articles(all_articles)
            except Exception as e:
                st.error(f"Analysis error: {e}")
                st.stop()

        source_count = len(set(a['source'] for a in all_articles))

        st.markdown(f"""
        <div class="article">
            <div class="kicker">
                <span>{today}</span>
                <span class="kicker-sep">—</span>
                <span>{source_count} Sources Analyzed</span>
                <span class="kicker-sep">—</span>
                <span>{len(all_articles)} Articles Reviewed</span>
            </div>
            <div class="headline">{analysis.get('headline', topic.title())}</div>
            <div class="summary">{analysis.get('summary', '')}</div>
            <div class="byline">
                <span class="byline-text">AI Analysis</span>
                <span class="byline-dot">·</span>
                <span class="byline-text">The Brief</span>
                <span class="byline-dot">·</span>
                <span class="byline-text">{today}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        data_points = analysis.get("data_points", [])
        if data_points:
            st.markdown('<div class="article">', unsafe_allow_html=True)
            st.markdown('<div class="sec-red">By The Numbers</div>', unsafe_allow_html=True)
            grid = '<div class="data-row">'
            for dp in data_points[:5]:
                grid += f'<div class="data-card"><div class="data-num">{dp.get("value","")}</div><div class="data-desc">{dp.get("context","")}</div><div class="data-src">{dp.get("source","")}</div></div>'
            grid += '</div>'
            st.markdown(grid, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="article">', unsafe_allow_html=True)
        st.markdown('<div class="sec">Key Findings</div>', unsafe_allow_html=True)
        for i, item in enumerate(analysis.get("key_insights", []), 1):
            insight = item.get("insight", "")
            importance = item.get("importance", "")
            st.markdown(f'<div class="finding"><div class="finding-n">Finding {i:02d}</div><div class="finding-body">{insight}</div><div class="finding-imp">{importance}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        quotes = analysis.get("quotes", [])
        if quotes:
            st.markdown('<div class="article">', unsafe_allow_html=True)
            st.markdown('<div class="sec">Notable Claims</div>', unsafe_allow_html=True)
            for q in quotes[:4]:
                qurl = q.get('url', '')
                qtext = q.get('text', '')
                qsource = q.get('source', '')
                qcontext = q.get('context', '')
                link = f'<a class="pq-link" href="{qurl}" target="_blank">Read full article</a>' if qurl else ''
                st.markdown(f'<div class="pq"><div class="pq-tag">Dispatch</div><div class="pq-text">"{qtext}"</div><div class="pq-source">{qsource}</div><div class="pq-context">{qcontext}</div>{link}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        timeline = analysis.get("timeline", [])
        if timeline:
            st.markdown('<div class="article">', unsafe_allow_html=True)
            st.markdown('<div class="sec">Chronology</div>', unsafe_allow_html=True)
            for item in timeline:
                tdate = item.get("date", "")
                tevent = item.get("event", "")
                tsig = item.get("significance", "")
                st.markdown(f'<div class="tl"><div class="tl-spine"><div class="tl-dot"></div><div class="tl-line"></div></div><div><div class="tl-date">{tdate}</div><div class="tl-event">{tevent}</div><div class="tl-sig">{tsig}</div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="article">', unsafe_allow_html=True)
        st.markdown('<div class="sec">Editorial Assessment</div>', unsafe_allow_html=True)
        for label, key in [("Where Sources Agree", "consensus"), ("Where They Diverge", "divergence"), ("Missing Perspectives", "missing_perspectives")]:
            body = analysis.get(key, "")
            st.markdown(f'<div class="assess"><div class="assess-tag">{label}</div><div class="assess-body">{body}</div></div><hr class="rule" style="margin:24px 0">', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="article">', unsafe_allow_html=True)
        st.markdown('<div class="sec">Source Breakdown</div>', unsafe_allow_html=True)
        for s in analysis.get("source_analysis", []):
            sentiment = s.get("sentiment", "Neutral").lower()
            bmap = {"positive": "stag-pos", "negative": "stag-neg", "neutral": "stag-neu", "mixed": "stag-mix"}
            bcls = bmap.get(sentiment, "stag-neu")
            sname = s.get("source", "")
            ssentiment = s.get("sentiment", "")
            sbias = s.get("bias", "")
            cred = s.get("credibility", 5)
            bar = "█" * cred + "░" * (10 - cred)
            sframe = s.get("framing", "")
            sangle = s.get("key_angle", "")
            st.markdown(f'<div class="src-prose"><div class="src-prose-header"><div class="src-prose-name">{sname}</div><div class="src-tags"><span class="stag {bcls}">{ssentiment}</span><span class="stag stag-neu">{sbias}</span></div></div><div class="src-cred"><b>{cred}/10</b> &nbsp;{bar}</div><div class="src-prose-text">{sframe}</div><div class="src-prose-angle">{sangle}</div></div>', unsafe_allow_html=True)
        st.markdown('<hr class="rule">', unsafe_allow_html=True)
        bias_summary = analysis.get("bias_summary", "")
        st.markdown(f'<div class="assess"><div class="assess-tag">Bias Report</div><div class="assess-body">{bias_summary}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="article">', unsafe_allow_html=True)
        st.markdown('<hr class="rule">', unsafe_allow_html=True)
        st.markdown('<div class="sec">All Articles Reviewed</div>', unsafe_allow_html=True)
        dispatches = ""
        for a in all_articles:
            aurl = a.get("url", "")
            atitle = a["title"]
            alinked = f'<a href="{aurl}" target="_blank">{atitle}</a>' if aurl else atitle
            asource = a["source"]
            adate = a.get("publishedAt", "")
            dispatches += f'<div class="dispatch"><div class="d-src">{asource}</div><div class="d-date">{adate}</div><div class="d-title">{alinked}</div></div>'
        st.markdown(dispatches, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div style="max-width:680px; margin:0 auto; padding:80px 40px; text-align:center;">
            <div style="font-family:'Playfair Display',serif; font-size:52px; font-weight:900; color:#1a1410; line-height:1.1; letter-spacing:-2px; margin-bottom:24px;">
                Go deeper on any topic.
            </div>
            <div style="font-family:'Source Serif 4',serif; font-size:18px; color:#8a7a6a; font-style:italic; line-height:1.8;">
                Enter any topic above and receive a full editorial brief — key findings, data, source analysis, and bias assessment — drawn from across the global press.
            </div>
        </div>
        """, unsafe_allow_html=True)

elif tab == "subscribe":
    st.markdown('<div class="sub-box">', unsafe_allow_html=True)
    st.markdown("""
    <div class="sub-title">Get The Brief in your inbox.</div>
    <div class="sub-desc">Subscribe to receive a daily intelligence brief — top world news, technology, business and politics — analyzed and delivered every morning and evening.</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sub-label">Your email address</div>', unsafe_allow_html=True)
    email = st.text_input("", placeholder="you@example.com", label_visibility="collapsed", key="sub_email")

    st.markdown('<div class="sub-label">Delivery schedule</div>', unsafe_allow_html=True)
    schedule = st.radio("", ["Morning only (8:00 AM)", "Evening only (7:00 PM)", "Both (8:00 AM + 7:00 PM)"], index=2, label_visibility="collapsed")
    schedule_key = "both" if "Both" in schedule else "morning" if "Morning" in schedule else "evening"

    st.markdown('<div class="sub-label">Topics</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        w = st.checkbox("🌍 World News", value=True)
        t = st.checkbox("💻 Technology", value=True)
    with col2:
        b = st.checkbox("📈 Business & Economy", value=True)
        p = st.checkbox("🏛 Politics", value=True)
    topics = [c for c, v in [("world", w), ("tech", t), ("business", b), ("politics", p)] if v]

    if st.button("Subscribe to The Brief →", use_container_width=True):
        if email and "@" in email:
            success, msg = add_subscriber(email, schedule_key, topics)
            if success:
                welcome_html = f"""
                <html><body style="font-family:Georgia,serif;background:#f5f0e8;padding:40px;">
                <div style="max-width:560px;margin:0 auto;background:#1a1410;padding:32px;text-align:center;">
                    <div style="font-size:32px;font-weight:900;color:#f5f0e8;">The <span style="color:#c1440e">Brief</span></div>
                </div>
                <div style="max-width:560px;margin:0 auto;padding:32px;background:#fff;">
                    <h2 style="color:#1a1410;">Welcome to The Brief.</h2>
                    <p style="color:#5a4a3a;line-height:1.8;">You're now subscribed to receive your daily intelligence brief at <b>{email}</b>.</p>
                    <p style="color:#5a4a3a;line-height:1.8;">Your first brief will arrive on schedule. Stay informed.</p>
                </div>
                </body></html>
                """
                from mailer import send_email
                send_email(email, "Welcome to The Brief", welcome_html)
                st.success(f"✓ Subscribed! Welcome email sent to {email}")
            else:
                st.info(f"ℹ️ {msg}")
        else:
            st.error("Please enter a valid email address.")

    subscribers = load_subscribers()
    if subscribers:
        st.markdown(f'<div class="sub-label" style="margin-top:48px;">Current subscribers — {len(subscribers)}</div>', unsafe_allow_html=True)
        for sub in subscribers:
            st.markdown(f'<div class="sub-row"><span>{sub["email"]}</span><span style="color:#8a7a6a;font-size:12px;">{sub["schedule"]} · {", ".join(sub["topics"])}</span></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
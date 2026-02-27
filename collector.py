import requests
import feedparser
from dotenv import load_dotenv
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def format_date(date_str):
    if not date_str:
        return "Date unknown"
    try:
        dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%b %d, %Y")
    except Exception:
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime("%b %d, %Y")
        except Exception:
            return date_str[:10] if len(date_str) >= 10 else date_str

def fetch_newsapi(topic):
    url = f'https://newsapi.org/v2/everything?q="{topic}"&language=en&pageSize=20&sortBy=relevancy&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url, timeout=10).json()
    except Exception:
        return []
    articles = []
    for a in response.get("articles", []):
        if a.get("title") and a.get("description"):
            title = a["title"].lower()
            desc = a["description"].lower()
            topic_words = [w for w in topic.lower().split() if len(w) > 3]
            if not topic_words:
                topic_words = topic.lower().split()
            matches = sum(1 for w in topic_words if w in title or w in desc)
            if matches >= max(1, len(topic_words)):
                articles.append({
                    "source": a["source"]["name"],
                    "title": a["title"],
                    "description": a["description"],
                    "url": a.get("url", ""),
                    "publishedAt": format_date(a.get("publishedAt", "")),
                    "urlToImage": a.get("urlToImage", ""),
                    "relevance_score": 90
                })
    return articles

RSS_FEEDS = {
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "AP News": "https://feeds.apnews.com/rss/apf-topnews",
    "NPR": "https://feeds.npr.org/1001/rss.xml",
    "Deutsche Welle": "https://rss.dw.com/rdf/rss-en-all",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "France 24": "https://www.france24.com/en/rss",
    "RFI English": "https://en.rfi.fr/general.rss",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Wired": "https://www.wired.com/feed/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "Le Monde (EN)": "https://www.lemonde.fr/en/rss/une.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "Euronews": "https://feeds.euronews.com/news/en",
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "Reuters World": "https://feeds.reuters.com/reuters/worldNews",
}

SOURCE_METADATA = {
    "BBC News": {"bias": "Center", "credibility": 9, "region": "UK"},
    "AP News": {"bias": "Center", "credibility": 10, "region": "US"},
    "NPR": {"bias": "Center-Left", "credibility": 9, "region": "US"},
    "Deutsche Welle": {"bias": "Center", "credibility": 8, "region": "Germany"},
    "Al Jazeera": {"bias": "Center", "credibility": 7, "region": "Qatar"},
    "France 24": {"bias": "Center", "credibility": 8, "region": "France"},
    "RFI English": {"bias": "Center", "credibility": 7, "region": "France"},
    "TechCrunch": {"bias": "Center", "credibility": 7, "region": "US"},
    "Wired": {"bias": "Center-Left", "credibility": 8, "region": "US"},
    "Ars Technica": {"bias": "Center-Left", "credibility": 8, "region": "US"},
    "MIT Tech Review": {"bias": "Center", "credibility": 9, "region": "US"},
    "Le Monde (EN)": {"bias": "Center-Left", "credibility": 9, "region": "France"},
    "The Guardian": {"bias": "Center-Left", "credibility": 8, "region": "UK"},
    "Euronews": {"bias": "Center", "credibility": 7, "region": "EU"},
    "Reuters Business": {"bias": "Center", "credibility": 10, "region": "UK"},
    "Reuters World": {"bias": "Center", "credibility": 10, "region": "UK"},
    "Fox News": {"bias": "Right", "credibility": 5, "region": "US"},
    "Yahoo Finance": {"bias": "Center", "credibility": 6, "region": "US"},
}

STOP_WORDS = {"the","a","an","is","in","of","on","at","to","for","and","or","but","with","about","from","are","was","were","has","have","had","its","it","this","that","be","by"}

def relevance_score(title, summary, keywords):
    combined = (title + " " + summary).lower()
    title_lower = title.lower()
    score = 0
    sig_kw = [k for k in keywords if k.lower() not in STOP_WORDS and len(k) > 2]
    if not sig_kw:
        sig_kw = keywords
    for kw in sig_kw:
        kw_lower = kw.lower()
        if kw_lower in title_lower:
            score += 50
        elif kw_lower in combined:
            score += 10
    if sig_kw and all(k.lower() in title_lower for k in sig_kw):
        score += 30
    return min(score, 100)

def fetch_rss(topic_keywords=None):
    articles = []

    def fetch_one(source, url):
        result = []
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= 5:
                    break
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                if topic_keywords:
                    score = relevance_score(title, summary, topic_keywords)
                    if score < 50:
                        continue
                meta = SOURCE_METADATA.get(source, {"bias": "Unknown", "credibility": 5, "region": "Unknown"})
                pub_date = entry.get("published", "") or entry.get("updated", "")
                result.append({
                    "source": source,
                    "title": title,
                    "description": summary[:300] if summary else "",
                    "url": entry.get("link", ""),
                    "publishedAt": format_date(pub_date),
                    "bias": meta["bias"],
                    "credibility": meta["credibility"],
                    "region": meta["region"],
                    "relevance_score": relevance_score(title, summary, topic_keywords) if topic_keywords else 100
                })
                count += 1
        except Exception:
            pass
        return result

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_one, source, url): source for source, url in RSS_FEEDS.items()}
        for future in as_completed(futures):
            articles.extend(future.result())

    if topic_keywords:
        articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return articles

def fetch_trending_topics():
    trending = []
    feeds = {
        "AP News": "https://feeds.apnews.com/rss/apf-topnews",
        "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
        "Reuters World": "https://feeds.reuters.com/reuters/worldNews",
    }
    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                if title:
                    trending.append({
                        "title": title,
                        "source": source,
                        "url": entry.get("link", "")
                    })
        except Exception:
            continue
    return trending[:15]

def fetch_stock_data(symbols=None):
    """Fetch live stock/market data via Yahoo Finance (no API key needed)."""
    if symbols is None:
        symbols = ["^GSPC", "^IXIC", "^DJI", "BTC-USD", "GC=F", "EURUSD=X"]
    results = []
    for symbol in symbols:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=6)
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0)
            prev = meta.get("previousClose", price)
            change = price - prev
            change_pct = (change / prev * 100) if prev else 0
            name_map = {
                "^GSPC": "S&P 500", "^IXIC": "NASDAQ", "^DJI": "Dow Jones",
                "BTC-USD": "Bitcoin", "GC=F": "Gold", "EURUSD=X": "EUR/USD"
            }
            results.append({
                "symbol": symbol,
                "name": name_map.get(symbol, symbol),
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "up": change >= 0
            })
        except Exception:
            continue
    return results

def enrich_with_metadata(articles):
    enriched = []
    for a in articles:
        source = a.get("source", "")
        meta = SOURCE_METADATA.get(source, {"bias": "Unknown", "credibility": 5, "region": "Unknown"})
        a["bias"] = meta.get("bias", "Unknown")
        a["credibility"] = meta.get("credibility", 5)
        a["region"] = meta.get("region", "Unknown")
        enriched.append(a)
    return enriched

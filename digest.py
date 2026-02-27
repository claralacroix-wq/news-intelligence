import feedparser
from datetime import datetime
from collector import SOURCE_METADATA, format_date

CATEGORY_FEEDS = {
    "world": {
        "BBC News": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "AP News": "https://feeds.apnews.com/rss/apf-topnews",
        "Reuters World": "https://feeds.reuters.com/reuters/worldNews",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "France 24": "https://www.france24.com/en/rss",
        "Deutsche Welle": "https://rss.dw.com/rdf/rss-en-all",
        "The Guardian": "https://www.theguardian.com/world/rss",
    },
    "tech": {
        "TechCrunch": "https://techcrunch.com/feed/",
        "Wired": "https://www.wired.com/feed/rss",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
        "MIT Tech Review": "https://www.technologyreview.com/feed/",
    },
    "business": {
        "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
        "NPR Business": "https://feeds.npr.org/1006/rss.xml",
        "BBC Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    },
    "politics": {
        "NPR Politics": "https://feeds.npr.org/1014/rss.xml",
        "BBC Politics": "http://feeds.bbci.co.uk/news/politics/rss.xml",
        "The Guardian Politics": "https://www.theguardian.com/politics/rss",
        "Euronews": "https://feeds.euronews.com/news/en",
    },
}

CATEGORY_LABELS = {
    "world": "Top World News",
    "tech": "Technology",
    "business": "Business & Economy",
    "politics": "Politics",
}

def fetch_category(category, max_per_source=3):
    feeds = CATEGORY_FEEDS.get(category, {})
    articles = []
    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= max_per_source:
                    break
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                link = entry.get("link", "")
                pub = entry.get("published", "") or entry.get("updated", "")
                if not title:
                    continue
                meta = SOURCE_METADATA.get(source, {"bias": "Unknown", "credibility": 5, "region": "Unknown"})
                articles.append({
                    "source": source,
                    "title": title,
                    "description": summary[:300] if summary else "",
                    "url": link,
                    "publishedAt": format_date(pub),
                    "bias": meta["bias"],
                    "credibility": meta["credibility"],
                    "region": meta["region"],
                    "category": category,
                })
                count += 1
        except Exception:
            continue
    return articles

def fetch_full_digest():
    digest = {}
    for category in CATEGORY_FEEDS:
        digest[category] = fetch_category(category)
    return digest

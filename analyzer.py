import anthropic
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def analyze_articles(articles):
    formatted = "\n\n".join([
        f"Source: {a['source']}\nTitle: {a['title']}\nDescription: {a['description']}\nURL: {a.get('url','')}\nBias: {a.get('bias','Unknown')}\nCredibility: {a.get('credibility','?')}/10"
        for a in articles
    ])

    prompt = f"""You are a senior news analyst. Analyze these {len(articles)} articles and return a JSON object.

CRITICAL RULES:
- Return ONLY raw JSON, no markdown, no backticks, no explanation
- All string values must use straight double quotes only
- No apostrophes anywhere — write "does not" instead of "doesn't", "it is" instead of "it's"
- No backslashes except in URLs
- Keep all text values simple and clean
- For data_points, extract REAL numbers/stats mentioned in the articles (percentages, dollar amounts, counts)
- For quotes, only include direct quotes actually present in the articles
- For source_analysis, include ALL sources present in the articles

Return this exact structure:
{{
  "headline": "string",
  "summary": "string (2-3 sentences max)",
  "key_insights": [
    {{"insight": "string", "importance": "string", "category": "one of: Politics|Technology|Economy|Society|Science|Environment"}}
  ],
  "quotes": [
    {{"text": "string", "source": "string", "url": "string", "context": "string"}}
  ],
  "source_analysis": [
    {{"source": "string", "sentiment": "Positive", "sentiment_score": 0.5, "framing": "string (1 sentence)", "key_angle": "string (5 words max)", "credibility": 8, "bias": "Center"}}
  ],
  "timeline": [
    {{"date": "string", "event": "string", "significance": "string (1 sentence)"}}
  ],
  "data_points": [
    {{"value": "string (the number/stat)", "context": "string (what it means)", "source": "string", "url": "string"}}
  ],
  "consensus": "string",
  "divergence": "string",
  "bias_summary": "string",
  "missing_perspectives": "string",
  "sentiment_breakdown": {{"positive": 30, "neutral": 50, "negative": 20}},
  "top_entities": ["entity1", "entity2", "entity3", "entity4", "entity5"]
}}

Articles to analyze:
{formatted}"""

    message = client.messages.create(
        
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
        system="You are a JSON API. You output only raw valid JSON with no markdown formatting, no code fences, no explanation. Never use apostrophes in output text."
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()

    start = raw.find('{')
    end = raw.rfind('}') + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raw = re.sub(r'\\(?!["\\/bfnrtu])', r'', raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raw = raw.replace('\u2019', '').replace('\u2018', '').replace('\u201c', '"').replace('\u201d', '"')
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {
                    "headline": "Analysis Unavailable",
                    "summary": "There was an issue parsing the analysis. Please try again.",
                    "key_insights": [],
                    "quotes": [],
                    "source_analysis": [],
                    "timeline": [],
                    "data_points": [],
                    "consensus": "",
                    "divergence": "",
                    "bias_summary": "",
                    "missing_perspectives": "",
                    "sentiment_breakdown": {"positive": 33, "neutral": 34, "negative": 33},
                    "top_entities": []
                }
            
                def generate_digest_summary(articles_by_category):
    import anthropic, os
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    all_headlines = []
    for category, articles in articles_by_category.items():
        for a in articles[:3]:
            all_headlines.append(f"[{category.upper()}] {a.get('title', '')}")
    
    headlines_text = "\n".join(all_headlines[:20])
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""You are an editor writing a morning briefing. Based on these headlines, write a 3-4 sentence summary of the most important stories of the day. Be direct, informative and authoritative. No bullet points — flowing prose only.

Headlines:
{headlines_text}

Write the briefing now:"""
        }]
    )
    return message.content[0].text

  
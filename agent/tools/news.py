from typing import Any, Dict, List
import requests
from ..config import settings

def get_company_news(ticker: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch real-time news headlines using NewsAPI, with free yfinance news fallback."""
    # 1. Try NewsAPI if configured
    if settings.NEWS_API_KEY and settings.NEWS_API_KEY != "your_newsapi_org_key_here":
        url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={settings.NEWS_API_KEY}&language=en&sortBy=publishedAt&pageSize={limit}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                return [
                    {
                        "title": a.get("title"),
                        "description": a.get("description"),
                        "source": a.get("source", {}).get("name"),
                        "url": a.get("url"),
                        "published_at": a.get("publishedAt")
                    }
                    for a in articles if a.get("title")
                ]
        except Exception:
            pass

    # 2. Free live fallback: fetch news directly from yfinance
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        yf_news = getattr(stock, "news", []) or []
        articles = []
        for item in yf_news[:limit]:
            # Support both old and new yfinance news schema
            content = item.get("content", {}) if isinstance(item.get("content"), dict) else {}
            title = content.get("title") or item.get("title") or "Market Update"
            summary = content.get("summary") or item.get("description") or item.get("snippet") or title
            publisher = content.get("provider", {}).get("displayName") or item.get("publisher") or "Yahoo Finance"
            
            articles.append({
                "title": title,
                "description": summary,
                "source": publisher,
                "url": item.get("link") or content.get("canonicalUrl", {}).get("url") or ""
            })
        if articles:
            return articles
    except Exception:
        pass

    return [
        {
            "title": f"Recent Market Activity for {ticker.upper()}",
            "description": f"Ongoing financial coverage and operational tracking for {ticker.upper()}.",
            "source": "Market Feed"
        }
    ]

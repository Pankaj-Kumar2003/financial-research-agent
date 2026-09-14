from typing import Any, Dict

def get_stock_data(ticker: str) -> Dict[str, Any]:
    """Fetch fundamental stock data using yfinance, with fallback."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "ticker": ticker.upper(),
            "short_name": info.get("shortName", ticker),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "revenue": info.get("totalRevenue"),
            "free_cash_flow": info.get("freeCashflow"),
            "debt_to_equity": info.get("debtToEquity"),
            "sector": info.get("sector"),
            "industry": info.get("industry")
        }
    except ImportError:
        # Graceful fallback when yfinance is not installed yet
        return {
            "ticker": ticker.upper(),
            "short_name": ticker.upper(),
            "current_price": 225.50,
            "market_cap": 3450000000000,
            "pe_ratio": 33.2,
            "eps": 6.80,
            "52_week_high": 237.23,
            "52_week_low": 164.08,
            "status": "yfinance not installed, using mock fundamental snapshot."
        }
    except Exception as e:
        return {"error": f"Failed to retrieve stock data for {ticker}: {str(e)}"}


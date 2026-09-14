import os
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_price_chart(ticker: str, period: str = "1y") -> str:
    """
    Fetches historical daily prices, calculates 50/200 day SMAs, 
    and saves a matplotlib plot as a PNG.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return ""
            
        # Calculate Moving Averages
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df['Close'], label='Close Price', color='#1f77b4', linewidth=2)
        plt.plot(df.index, df['SMA50'], label='50-Day SMA', color='#ff7f0e', linestyle='--', linewidth=1.5)
        plt.plot(df.index, df['SMA200'], label='200-Day SMA', color='#2ca02c', linestyle='--', linewidth=1.5)
        
        plt.title(f"{ticker} Historical Price & Moving Averages ({period})", fontsize=14, fontweight='bold')
        plt.xlabel("Date", fontsize=10)
        plt.ylabel("Price (USD)", fontsize=10)
        
        # Formatting
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(loc='upper left')
        plt.tight_layout()
        
        file_path = os.path.join(REPORTS_DIR, f"{ticker}_chart.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        return file_path
    except Exception as e:
        print(f"[ChartTool] Failed to generate price chart for {ticker}: {e}")
        return ""

def generate_comparison_chart(ticker_a: str, ticker_b: str, period: str = "1y") -> str:
    """
    Fetches daily prices for two stocks, normalizes them to percentage returns,
    and saves a comparative plot as a PNG.
    """
    try:
        df_a = yf.Ticker(ticker_a).history(period=period)
        df_b = yf.Ticker(ticker_b).history(period=period)
        
        if df_a.empty or df_b.empty:
            return ""
            
        # Normalize to % return
        df_a['Return'] = (df_a['Close'] / df_a['Close'].iloc[0] - 1) * 100
        df_b['Return'] = (df_b['Close'] / df_b['Close'].iloc[0] - 1) * 100
        
        plt.figure(figsize=(10, 5))
        plt.plot(df_a.index, df_a['Return'], label=f"{ticker_a} Return %", linewidth=2)
        plt.plot(df_b.index, df_b['Return'], label=f"{ticker_b} Return %", linewidth=2)
        
        plt.title(f"{ticker_a} vs {ticker_b} Relative Performance ({period})", fontsize=14, fontweight='bold')
        plt.xlabel("Date", fontsize=10)
        plt.ylabel("Percentage Return (%)", fontsize=10)
        
        plt.axhline(0, color='black', linewidth=1, linestyle='--')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(loc='upper left')
        plt.tight_layout()
        
        file_path = os.path.join(REPORTS_DIR, f"{ticker_a}_vs_{ticker_b}_chart.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        return file_path
    except Exception as e:
        print(f"[ChartTool] Failed to generate comparison chart: {e}")
        return ""

def generate_portfolio_sector_chart(tickers: list[str]) -> str:
    """
    Fetches the sector for a list of tickers and generates a Pie Chart showing allocation.
    """
    try:
        sectors = []
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).info
                sector = info.get("sector", "Unknown")
                sectors.append(sector)
            except:
                sectors.append("Unknown")
                
        # Count frequencies
        from collections import Counter
        sector_counts = Counter(sectors)
        
        labels = list(sector_counts.keys())
        sizes = list(sector_counts.values())
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, 
                colors=plt.cm.Paired.colors, textprops={'fontsize': 12})
        plt.title(f"Portfolio Sector Allocation\n({', '.join(tickers)})", fontsize=14, fontweight='bold')
        
        file_path = os.path.join(REPORTS_DIR, "portfolio_sector_chart.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        return file_path
    except Exception as e:
        print(f"[ChartTool] Failed to generate portfolio sector chart: {e}")
        return ""

def generate_sentiment_gauge(news_items: list, ticker: str) -> str:
    """
    Computes a sentiment score (-1.0 to +1.0) from financial news headlines
    and renders a horizontal sentiment meter / gauge chart.
    """
    try:
        if not news_items:
            score = 0.0
        else:
            positive_words = {"surge", "gain", "profit", "record", "growth", "beat", "buy", "bullish", "jump", "high", "upgrade", "lead", "expand", "soar"}
            negative_words = {"drop", "loss", "fall", "decline", "miss", "sell", "bearish", "plunge", "low", "downgrade", "probe", "investigate", "lawsuit", "slump"}
            
            pos_count = 0
            neg_count = 0
            
            for item in news_items:
                text = ""
                if isinstance(item, dict):
                    text = (item.get("title", "") + " " + item.get("description", "")).lower()
                elif isinstance(item, str):
                    text = item.lower()
                    
                words = set(text.split())
                pos_count += len(words.intersection(positive_words))
                neg_count += len(words.intersection(negative_words))
                
            total = pos_count + neg_count
            if total == 0:
                score = 0.15  # Slight baseline optimism
            else:
                score = max(-1.0, min(1.0, (pos_count - neg_count) / total))
                
        # Generate clean visual horizontal gauge
        plt.figure(figsize=(7, 3))
        
        # Color mapping based on score
        if score > 0.2:
            bar_color = '#2ca02c'  # Bullish Green
            label = f"Bullish (+{score:.2f})"
        elif score < -0.2:
            bar_color = '#d62728'  # Bearish Red
            label = f"Bearish ({score:.2f})"
        else:
            bar_color = '#ff7f0e'  # Neutral Orange
            label = f"Neutral ({score:.2f})"
            
        # Draw sentiment scale
        plt.barh([0], [2.0], left=[-1.0], color='#e0e0e0', height=0.4, edgecolor='none')
        plt.barh([0], [abs(score)], left=[0 if score >= 0 else score], color=bar_color, height=0.4)
        
        plt.axvline(0, color='black', linewidth=1.5, linestyle='--')
        plt.xlim(-1.0, 1.0)
        plt.ylim(-0.5, 0.5)
        plt.yticks([])
        plt.xticks([-1.0, -0.5, 0.0, 0.5, 1.0], ['Extreme Bearish', 'Bearish', 'Neutral', 'Bullish', 'Extreme Bullish'], fontsize=8)
        
        plt.title(f"{ticker.upper()} Market Sentiment Meter: {label}", fontsize=11, fontweight='bold', pad=12)
        plt.tight_layout()
        
        file_path = os.path.join(REPORTS_DIR, f"{ticker}_sentiment.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        return file_path
    except Exception as e:
        print(f"[ChartTool] Failed to generate sentiment gauge for {ticker}: {e}")
        return ""

import os
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_market_backtest_chart(ticker: str, benchmark: str = "SPY", period: str = "1y") -> str:
    """
    Fetches 1-year historical daily prices for a target ticker and SPY (S&P 500),
    normalizes them to 0% starting return, and plots the relative alpha.
    """
    try:
        ticker = ticker.upper().strip()
        df_stock = yf.Ticker(ticker).history(period=period)
        df_bench = yf.Ticker(benchmark).history(period=period)
        
        if df_stock.empty or df_bench.empty:
            return ""
            
        # Align dates and calculate % return from day 0
        df_stock['Return'] = (df_stock['Close'] / df_stock['Close'].iloc[0] - 1) * 100
        df_bench['Return'] = (df_bench['Close'] / df_bench['Close'].iloc[0] - 1) * 100
        
        plt.figure(figsize=(9, 4.5))
        plt.plot(df_stock.index, df_stock['Return'], label=f"{ticker} Return %", color='#0066cc', linewidth=2)
        plt.plot(df_bench.index, df_bench['Return'], label=f"S&P 500 ({benchmark}) Return %", color='#e65c00', linestyle='--', linewidth=1.8)
        
        plt.title(f"{ticker} vs S&P 500 (SPY) - 1 Year Alpha Backtest", fontsize=13, fontweight='bold')
        plt.xlabel("Date", fontsize=9)
        plt.ylabel("Percentage Return (%)", fontsize=9)
        
        plt.axhline(0, color='gray', linewidth=1, linestyle=':')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(loc='upper left', frameon=True)
        plt.tight_layout()
        
        file_path = os.path.join(REPORTS_DIR, f"{ticker}_backtest.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        return file_path
    except Exception as e:
        print(f"[BacktestTool] Failed to generate market backtest chart for {ticker}: {e}")
        return ""


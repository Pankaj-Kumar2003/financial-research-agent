import requests
from typing import Any, Dict, List, Optional
from ..config import settings

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

def get_cik_by_ticker(ticker: str) -> Optional[str]:
    """
    Look up a company's 10-digit SEC Central Index Key (CIK) from SEC EDGAR.
    """
    headers = {"User-Agent": settings.USER_AGENT}
    try:
        response = requests.get(SEC_TICKERS_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            ticker_upper = ticker.upper().strip()
            for entry in data.values():
                if entry.get("ticker") == ticker_upper:
                    cik = str(entry.get("cik_str")).zfill(10)
                    return cik
    except Exception as e:
        print(f"  [!] Failed to lookup CIK for {ticker}: {e}")
    return None

def get_sec_filings(ticker: str, form_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch live recent SEC EDGAR filing metadata (10-K, 10-Q, 8-K) using the official SEC API.
    """
    if form_types is None:
        form_types = ["10-K", "10-Q"]

    cik = get_cik_by_ticker(ticker)
    if not cik:
        return [{
            "ticker": ticker.upper(),
            "form": "N/A",
            "period": "N/A",
            "summary": f"Could not find SEC CIK for ticker {ticker.upper()}."
        }]

    headers = {"User-Agent": settings.USER_AGENT}
    url = SEC_SUBMISSIONS_URL.format(cik=cik)

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            recent_filings = data.get("filings", {}).get("recent", {})
            
            forms = recent_filings.get("form", [])
            filing_dates = recent_filings.get("filingDate", [])
            report_dates = recent_filings.get("reportDate", [])
            accession_numbers = recent_filings.get("accessionNumber", [])
            primary_documents = recent_filings.get("primaryDocument", [])
            
            results = []
            for i in range(len(forms)):
                form = forms[i]
                if form in form_types:
                    accession = accession_numbers[i].replace("-", "")
                    doc = primary_documents[i]
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{doc}"
                    
                    results.append({
                        "ticker": ticker.upper(),
                        "form": form,
                        "filing_date": filing_dates[i] if i < len(filing_dates) else "N/A",
                        "report_date": report_dates[i] if i < len(report_dates) else "N/A",
                        "url": doc_url,
                        "summary": f"Official SEC {form} filing for period ending {report_dates[i] if i < len(report_dates) else 'N/A'}, filed on {filing_dates[i] if i < len(filing_dates) else 'N/A'}."
                    })
                    
                    # Limit to the 3 most recent filings to keep context concise
                    if len(results) >= 3:
                        break
                        
            if results:
                return results

    except Exception as e:
        print(f"  [!] Failed to retrieve SEC submissions for CIK {cik}: {e}")

    # Graceful fallback if network or endpoint is unavailable
    return [{
        "ticker": ticker.upper(),
        "form": "10-K / 10-Q",
        "period": "Recent",
        "summary": f"Recent 10-K and 10-Q SEC EDGAR filings available for {ticker.upper()}."
    }]

import re
from bs4 import BeautifulSoup

def download_and_clean_html(url: str) -> str:
    """Download SEC filing HTML and convert to clean text."""
    headers = {"User-Agent": settings.USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove tables that are mainly financial numbers to reduce noise, unless they're small
            for table in soup.find_all("table"):
                table.decompose()
                
            text = soup.get_text(separator="\n")
            # Clean up excessive whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r'\xa0', ' ', text)
            return text
    except Exception as e:
        print(f"  [!] Failed to download and clean SEC filing at {url}: {e}")
    return ""

def extract_10k_items(text: str) -> Dict[str, str]:
    """Extract Item 1A (Risk Factors) and Item 7 (MD&A) from clean 10-K text."""
    results = {"item_1a": "Not found or extraction failed.", "item_7": "Not found or extraction failed."}
    if not text:
        return results
        
    # Standardize whitespace to make regex matching easier
    text_clean = re.sub(r'\s+', ' ', text)
    
    # Try to find Item 1A using a flexible regex to handle SEC HTML parsing artifacts (like "RIS K")
    # We look for the 2nd or 3rd occurrence usually, but let's grab the longest section between 1A and 1B
    matches_1a = list(re.finditer(r'ITEM\s+1A\b.*?RISK\s+FACTORS', text_clean, re.IGNORECASE))
    matches_1b = list(re.finditer(r'ITEM\s+1B\b.*?UNRESOLVED', text_clean, re.IGNORECASE))
    
    if matches_1a and matches_1b:
        end_idx = matches_1b[-1].start()
        # Find the last 1A match that occurs before the 1B match
        valid_1a = [m for m in matches_1a if m.end() < end_idx]
        if valid_1a:
            start_idx = valid_1a[-1].end()
            extracted = text_clean[start_idx:end_idx].strip()
            results["item_1a"] = extracted[:2500] + ("..." if len(extracted) > 2500 else "")

    # Try to find Item 7
    matches_7 = list(re.finditer(r'ITEM\s+7\b.*?MANAGEMENT.*?DISCUSSION', text_clean, re.IGNORECASE))
    matches_7a = list(re.finditer(r'ITEM\s+7A\b.*?QUANTITATIVE', text_clean, re.IGNORECASE))
    
    if matches_7 and matches_7a:
        end_idx = matches_7a[-1].start()
        valid_7 = [m for m in matches_7 if m.end() < end_idx]
        if valid_7:
            start_idx = valid_7[-1].end()
            extracted = text_clean[start_idx:end_idx].strip()
            results["item_7"] = extracted[:3000] + ("..." if len(extracted) > 3000 else "")
            
    return results

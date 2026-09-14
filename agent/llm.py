import os
import json
import time
import re
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from .config import settings

def call_llm_rest(prompt: str, system_instruction: Optional[str] = None, max_retries: int = 5) -> str:
    """Direct HTTP REST call to Groq (primary) and OpenRouter (fallback) OpenAI-compatible APIs."""
    providers = []
    if settings.GROQ_API_KEY:
        providers.append({
            "name": "Groq",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "key": settings.GROQ_API_KEY,
            "model": "qwen/qwen3.8-27b"
        })
    if settings.OPENROUTER_API_KEY:
        providers.append({
            "name": "OpenRouter",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "key": settings.OPENROUTER_API_KEY,
            "model": "meta-llama/llama-3.3-70b-instruct"
        })
        
    if not providers:
        raise ValueError("Neither GROQ_API_KEY nor OPENROUTER_API_KEY is set in .env")

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    errors = []
    for provider in providers:
        payload = {
            "model": provider["model"],
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800
        }
        data = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['key']}",
            "User-Agent": settings.USER_AGENT
        }
        
        provider_error = None
        for attempt in range(max_retries):
            req = urllib.request.Request(
                provider["url"],
                data=data,
                headers=headers
            )
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    choices = result.get("choices", [])
                    if choices:
                        message = choices[0].get("message", {})
                        if "content" in message:
                            text = message["content"]
                            return text.strip()
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                provider_error = f"{provider['name']} (HTTP {e.code}): {err_body}"
                
                if e.code == 429:
                    print(f"  [!] Rate limit on {provider['name']}. Waiting 15s...")
                    time.sleep(15)
                    continue
                elif e.code in (500, 502, 503, 504):
                    time.sleep(2)
                    continue
                else:
                    break
            except Exception as e:
                provider_error = f"{provider['name']}: {str(e)}"
                time.sleep(1)
                continue
                
        if provider_error:
            errors.append(provider_error)

    raise RuntimeError(f"LLM API request failed across all providers:\n" + "\n".join(errors))

def call_llm_chat(messages: List[Dict[str, str]], max_retries: int = 5) -> str:
    """Direct HTTP REST call using a full conversational message history."""
    providers = []
    if settings.GROQ_API_KEY:
        providers.append({
            "name": "Groq",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "key": settings.GROQ_API_KEY,
            "model": "qwen/qwen3.8-27b"
        })
    if settings.OPENROUTER_API_KEY:
        providers.append({
            "name": "OpenRouter",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "key": settings.OPENROUTER_API_KEY,
            "model": "meta-llama/llama-3.3-70b-instruct"
        })
        
    if not providers:
        raise ValueError("Neither GROQ_API_KEY nor OPENROUTER_API_KEY is set in .env")

    errors = []
    for provider in providers:
        payload = {
            "model": provider["model"],
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 800
        }
        data = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['key']}",
            "User-Agent": settings.USER_AGENT
        }
        
        provider_error = None
        for attempt in range(max_retries):
            req = urllib.request.Request(
                provider["url"],
                data=data,
                headers=headers
            )
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    choices = result.get("choices", [])
                    if choices:
                        message = choices[0].get("message", {})
                        if "content" in message:
                            return message["content"].strip()
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                provider_error = f"{provider['name']} (HTTP {e.code}): {err_body}"
                
                if e.code == 429:
                    time.sleep(15)
                    continue
                elif e.code in (500, 502, 503, 504):
                    time.sleep(2)
                    continue
                else:
                    break
            except Exception as e:
                provider_error = f"{provider['name']}: {str(e)}"
                time.sleep(1)
                continue
                
        if provider_error:
            errors.append(provider_error)

    raise RuntimeError(f"Chat LLM API request failed across all providers:\n" + "\n".join(errors))

def generate_full_investment_brief(context: str, ticker: str) -> Dict[str, str]:
    """
    Generate all 6 investment brief sections in a single optimized LLM synthesis pass.
    """
    system_inst = (
        "You are an expert Wall Street research analyst. "
        "Synthesize the provided company context into a thorough, professional 6-section Investment Brief. "
        "Do not hallucinate numbers or claims not present in the context. "
        "Output ONLY the final 6 markdown sections without preamble."
    )
    
    prompt = (
        f"Analyze the following data for ticker {ticker} and generate the 6-section Investment Brief.\n\n"
        f"Context:\n{context}\n\n"
        f"Format your output strictly with these exact markdown headers:\n\n"
        f"## Executive Summary\n<Executive summary content>\n\n"
        f"## Financial Health\n<Financial health and valuation analysis>\n\n"
        f"## Recent Developments\n<Recent news and developments>\n\n"
        f"## SEC Filing Highlights\n<Summary of SEC filing metadata and reports>\n\n"
        f"## Risk Factors\n<Key fundamental, operational, and valuation risks>\n\n"
        f"## Outlook\n<Forward outlook and synthesis>\n"
    )
    
    raw_response = call_llm_rest(prompt=prompt, system_instruction=system_inst)
    
    sections_order = [
        "Executive Summary",
        "Financial Health",
        "Recent Developments",
        "SEC Filing Highlights",
        "Risk Factors",
        "Outlook"
    ]
    
    brief: Dict[str, str] = {}
    for i, sec in enumerate(sections_order):
        pattern = rf"##\s*{re.escape(sec)}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, raw_response, re.DOTALL | re.IGNORECASE)
        if match and match.group(1).strip():
            brief[sec] = match.group(1).strip()
        else:
            brief[sec] = "Section synthesized within brief."
            
    return brief

def generate_section(context: str, section_name: str) -> str:
    """Generate a single specific section."""
    system_inst = "You are an expert Wall Street financial research analyst. Synthesize context accurately without hallucinating."
    prompt = f"Based on the following context, write the '{section_name}' section of an investment brief.\n\nContext:\n{context}"
    return call_llm_rest(prompt=prompt, system_instruction=system_inst)

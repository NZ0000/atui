#!/usr/bin/env python3
"""
Tool: web_search
Performs live internet search to find documentation, code snippets, algorithms,
and technical implementations.
Supports DuckDuckGo (ddgs), HTML fallbacks, and content fetching.
"""

import sys
import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner
except ImportError:
    from base import make_result, cli_runner

TOOL_SPEC = {
    "name": "web_search",
    "description": "Search the internet for technical solutions, Three.js/WebGL techniques, libraries, documentation, and code examples.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query keywords (e.g. 'Three.js procedural greeble normal map canvas', 'UnrealBloomPass setup')."
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of search results to return. Default is 5."
            },
            "fetch_url": {
                "type": "string",
                "description": "Optional specific URL to fetch and extract text content from."
            }
        },
        "required": ["query"]
    }
}

def fetch_page_text(url: str, max_chars: int = 4000) -> str:
    """Extract clean text content from a webpage URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            clean = "\n".join(lines)
            return clean[:max_chars]
        except Exception:
            return html[:max_chars]
    except Exception as e:
        return f"[Error fetching {url}: {e}]"

def search_internet(query: str, max_results: int = 5, fetch_url: Optional[str] = None) -> Dict[str, Any]:
    if fetch_url:
        page_text = fetch_page_text(fetch_url)
        return make_result(True, data={
            "url": fetch_url,
            "content": page_text
        })

    if not query:
        return make_result(False, error="Parameter 'query' cannot be empty.")

    results: List[Dict[str, Any]] = []

    # 1. Try ddgs library
    try:
        from ddgs import DDGS
        ddgs_client = DDGS(timeout=10)
        raw_items = list(ddgs_client.text(query, max_results=max_results))
        for item in raw_items:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")
            })
    except Exception as e:
        pass

    # 2. Fallback: DuckDuckGo HTML Lite scraping if ddgs failed
    if not results:
        try:
            from bs4 import BeautifulSoup
            encoded_q = urllib.parse.quote_plus(query)
            lite_url = f"https://lite.duckduckgo.com/lite/?q={encoded_q}"
            req = urllib.request.Request(
                lite_url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            links = soup.select(".result-link")
            snippets = soup.select(".result-snippet")
            for idx in range(min(len(links), max_results)):
                t = links[idx].get_text(strip=True)
                href = links[idx].get("href", "")
                snip = snippets[idx].get_text(strip=True) if idx < len(snippets) else ""
                results.append({"title": t, "url": href, "snippet": snip})
        except Exception:
            pass

    return make_result(
        len(results) > 0,
        data={
            "query": query,
            "total_found": len(results),
            "results": results
        },
        error="" if len(results) > 0 else f"No search results found for query: '{query}'."
    )

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    query = params.get("query", "")
    max_results = params.get("max_results", 5)
    fetch_url = params.get("fetch_url")
    return search_internet(query, max_results, fetch_url)

if __name__ == "__main__":
    cli_runner("web_search", TOOL_SPEC, execute)

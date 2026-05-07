"""Multi-source research — anti-hallucination gate.

Supports: Bing Search, Baidu Search, Custom keywords, Quality filtering.

Customization:
- custom_keywords: 手动指定搜索关键词
- min_snippet_length: 最小snippet长度筛选
- max_snippets: 最大返回数量
- quality_filter: 质量筛选函数
"""

import requests
import json
from html.parser import HTMLParser
from typing import Callable

from .config import extract_keywords, load_config
from .log import log
from .retry import with_retry


@with_retry(max_retries=2, base_delay=2.0)
def _fetch_bing(keywords: str) -> str:
    """Fetch search snippets from Bing (国内可访问)."""
    url = "https://www.bing.com/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    params = {"q": keywords, "count": 10}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    return r.text


@with_retry(max_retries=2, base_delay=2.0)
def _fetch_baidu(keywords: str) -> str:
    """Fetch search snippets from Baidu (国内)."""
    url = "https://www.baidu.com/s"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    params = {"wd": keywords, "rn": 10}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    return r.text


def _parse_bing_snippets(html: str) -> list[str]:
    """Extract snippets from Bing search results."""
    snippets = []

    class BingParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self._in_result = False
            self._in_snippet = False
            self._text = []

        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            class_attr = d.get("class", "")
            if tag == "p" and ("b_algo" in str(d.get("parent_class", "")) or True):
                self._in_snippet = True
                self._text = []
            elif tag == "span" and "algoSlug_icon" not in class_attr:
                self._in_snippet = True
                self._text = []

        def handle_endtag(self, tag):
            if self._in_snippet and tag in ("p", "span", "div"):
                text = "".join(self._text).strip()
                if text and len(text) > 20:
                    snippets.append(text)
                self._in_snippet = False

        def handle_data(self, data):
            if self._in_snippet:
                self._text.append(data)

    p = BingParser()
    p.feed(html)
    return snippets


def _parse_baidu_snippets(html: str) -> list[str]:
    """Extract snippets from Baidu search results."""
    snippets = []

    class BaiduParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self._in_content = False
            self._text = []

        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            class_attr = d.get("class", "")
            if "content-right" in class_attr or "c-abstract" in class_attr:
                self._in_content = True
                self._text = []

        def handle_endtag(self, tag):
            if self._in_content and tag == "div":
                text = "".join(self._text).strip()
                if text and len(text) > 20:
                    snippets.append(text)
                self._in_content = False

        def handle_data(self, data):
            if self._in_content:
                self._text.append(data)

    p = BaiduParser()
    p.feed(html)
    return snippets


def default_quality_filter(snippet: str) -> bool:
    """默认质量筛选: 排除广告、导航链接等."""
    # 排除太短的
    if len(snippet) < 30:
        return False
    # 排除常见广告词
    ad_words = ["广告", "推广", "sponsor", "advertisement", "点击购买"]
    if any(w in snippet.lower() for w in ad_words):
        return False
    # 排除纯导航链接
    if snippet.startswith("http") or snippet.startswith("www."):
        return False
    return True


def research_topic(
    news: str,
    custom_keywords: str = None,
    max_snippets: int = 8,
    min_snippet_length: int = 50,
    quality_filter: Callable[[str], bool] = None,
    source: str = "bing",
) -> str:
    """Multi-source search -> extract facts for anti-hallucination gate.

    Args:
        news: Topic or news headline
        custom_keywords: 手动指定搜索关键词 (优先于自动提取)
        max_snippets: 最大返回snippet数量
        min_snippet_length: 最小snippet长度
        quality_filter: 质量筛选函数，返回True保留
        source: 搜索源 (bing, baidu, auto)

    Returns:
        拼接的research文本，供LLM使用
    """
    log("Researching topic...")

    # 使用自定义关键词或自动提取
    keywords = custom_keywords or extract_keywords(news)
    log(f"Search keywords: {keywords}")

    quality_filter = quality_filter or default_quality_filter
    snippets = []

    # Try Bing first
    if source in ("bing", "auto"):
        try:
            html = _fetch_bing(keywords)
            raw_snippets = _parse_bing_snippets(html)
            # 质量筛选
            snippets = [s for s in raw_snippets if quality_filter(s)]
            # 长度筛选
            snippets = [s for s in snippets if len(s) >= min_snippet_length]
            log(f"Found {len(snippets)} quality snippets from Bing.")
        except Exception as e:
            log(f"Bing search failed: {e}")

    # Fallback to Baidu
    if not snippets and source in ("baidu", "auto"):
        try:
            html = _fetch_baidu(keywords)
            raw_snippets = _parse_baidu_snippets(html)
            snippets = [s for s in raw_snippets if quality_filter(s)]
            snippets = [s for s in snippets if len(s) >= min_snippet_length]
            log(f"Found {len(snippets)} quality snippets from Baidu.")
        except Exception as e:
            log(f"Baidu search failed: {e}")

    if snippets:
        # 截断每条snippet，限制prompt长度
        snippets = [s[:300] for s in snippets[:max_snippets]]
        return "\n".join(snippets)

    log("Research failed — proceeding without live data.")
    return f"Topic: {news}\n(No live research available — script must stay general.)"
# core/scrapers/coingecko/main_cg_scraper.py
"""
CoinGecko scraper entrypoint placeholder.

This module defines the public scrape_coingecko_data(query) API expected by the router.
Per docs/plan.md, CoinGecko is not yet implemented; we raise a clear NotImplementedError
so callers can handle it gracefully.
"""
from typing import Dict, List, Any


def scrape_coingecko_data(query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Placeholder for CoinGecko scraping.

    Args:
        query: Parameters controlling the scrape.

    Returns:
        No return on success; currently raises NotImplementedError.

    Raises:
        NotImplementedError: Always, until implemented.
    """
    print("CoinGecko scraping requested but not implemented yet")
    raise NotImplementedError("CoinGecko scraping is not implemented yet")

"""
Financial data provider package.

Provides a registry of available data providers in priority order.
"""

from typing import List
from .base import BaseProvider, ProviderResult, ProviderStatus, DataType


def get_provider_chain(settings) -> List[BaseProvider]:
    """Build ordered list of available providers based on configuration."""
    providers = []

    if getattr(settings, 'alpha_vantage_api_key', None):
        from .alpha_vantage import AlphaVantageProvider
        providers.append(AlphaVantageProvider(settings))

    if getattr(settings, 'fmp_api_key', None):
        from .fmp import FMPProvider
        providers.append(FMPProvider(settings))

    if getattr(settings, 'eulerpool_api_key', None):
        from .eulerpool import EulerpoolProvider
        providers.append(EulerpoolProvider(settings))

    try:
        import yfinance  # Verify the library is actually installed
        from .yfinance_provider import YFinanceProvider
        providers.append(YFinanceProvider(settings))
    except ImportError:
        pass

    return sorted(providers, key=lambda p: p.priority)

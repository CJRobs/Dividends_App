"""
Configuration management for the Dividend Portfolio Dashboard.

This module centralizes all configuration settings and provides
secure environment variable handling.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # API Configuration
    alpha_vantage_api_key: str
    
    # Application Settings
    default_currency: str = "GBP"
    default_theme: str = "Light"
    default_forecast_months: int = 12
    
    # Cache Settings
    cache_ttl_hours: int = 1
    
    # API Settings
    api_base_url: str = "https://www.alphavantage.co/query"
    api_rate_limit_delay: float = 0.2
    
    # UI Settings
    page_title: str = "Dividend Portfolio Dashboard"
    page_icon: str = "📈"
    layout: str = "wide"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables."""
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
        
        return cls(
            alpha_vantage_api_key=api_key,
            default_currency=os.getenv('DEFAULT_CURRENCY', 'GBP'),
            default_theme=os.getenv('DEFAULT_THEME', 'Light'),
            default_forecast_months=int(os.getenv('DEFAULT_FORECAST_MONTHS', '12')),
            cache_ttl_hours=int(os.getenv('CACHE_TTL_HOURS', '1')),
        )


# Currency symbols mapping
CURRENCY_SYMBOLS: Dict[str, str] = {
    'GBP': '£',
    'USD': '$',
    'EUR': '€',
    'JPY': '¥',
    'CAD': 'C$',
    'AUD': 'A$'
}

# Month names mapping
MONTH_NAMES: Dict[int, str] = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

# Ordered month list for consistent display
MONTH_ORDER: list[str] = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]


def load_config() -> AppConfig:
    """Load application configuration."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # dotenv not available, rely on system environment variables
        pass
    
    return AppConfig.from_env()


def get_currency_symbol(currency: str) -> str:
    """Get currency symbol for a given currency code."""
    return CURRENCY_SYMBOLS.get(currency.upper(), currency)


def format_currency(value: float, currency: str = 'GBP') -> str:
    """Format values as currency with appropriate symbol."""
    symbol = get_currency_symbol(currency)
    return f"{symbol}{value:,.2f}"
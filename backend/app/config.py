"""
Configuration management for the Dividend Portfolio Dashboard API.

This module centralizes all configuration settings using Pydantic Settings
for secure environment variable handling.
"""

from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Alpha Vantage API
    alpha_vantage_api_key: str
    api_base_url: str = "https://www.alphavantage.co/query"
    api_rate_limit_delay: float = 0.2

    # Application Settings
    default_currency: str = "GBP"
    default_forecast_months: int = 12

    # Cache Settings
    cache_ttl_hours: int = 1

    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Data Path
    data_path: str = "../data/dividends.csv"

    # Environment
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Currency symbols mapping
CURRENCY_SYMBOLS: Dict[str, str] = {
    "GBP": "£",
    "USD": "$",
    "EUR": "€",
    "JPY": "¥",
    "CAD": "C$",
    "AUD": "A$",
}

# Month names mapping
MONTH_NAMES: Dict[int, str] = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

# Ordered month list for consistent display
MONTH_ORDER: list[str] = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_currency_symbol(currency: str) -> str:
    """Get currency symbol for a given currency code."""
    return CURRENCY_SYMBOLS.get(currency.upper(), currency)


def format_currency(value: float, currency: str = "GBP") -> str:
    """Format values as currency with appropriate symbol."""
    symbol = get_currency_symbol(currency)
    return f"{symbol}{value:,.2f}"

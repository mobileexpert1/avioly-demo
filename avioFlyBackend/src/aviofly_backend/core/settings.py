from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str
    default_locale: str
    page_size: int
    cache_size: int


def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("AVIOFLY_APP_NAME", "avioFly"),
        default_locale=os.getenv("AVIOFLY_DEFAULT_LOCALE", "en"),
        page_size=int(os.getenv("AVIOFLY_PAGE_SIZE", "20")),
        cache_size=int(os.getenv("AVIOFLY_CACHE_SIZE", "50")),
    )


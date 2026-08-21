from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bfl_names: tuple[str, ...] = ()
    bfl_gstins: tuple[str, ...] = ()
    bfl_addresses: tuple[str, ...] = ()
    ocr_language: str = "eng"
    ocr_timeout: int = 30


def load_settings() -> Settings:
    def values(name: str) -> tuple[str, ...]:
        return tuple(value.strip() for value in os.getenv(name, "").split("|") if value.strip())

    return Settings(
        bfl_names=values("BFL_NAMES"),
        bfl_gstins=values("BFL_GSTINS"),
        bfl_addresses=values("BFL_ADDRESSES"),
        ocr_language=os.getenv("OCR_LANGUAGE", "eng"),
        ocr_timeout=int(os.getenv("OCR_TIMEOUT", "30")),
    )

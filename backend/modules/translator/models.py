"""
Pydantic models, constants, and validation helpers for the Translator module.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# ISO 639-1 language code whitelist & domain validation
# ---------------------------------------------------------------------------

VALID_LANG_CODES: set[str] = {
    "en", "ro", "de", "fr", "es", "it", "pt", "nl", "pl", "cs",
    "ja", "zh", "ko", "ru", "ar", "hi", "tr", "sv", "da", "no",
    "fi", "hu", "bg", "el", "uk", "hr", "sk", "sl", "et", "lv",
    "lt", "ga", "mt", "sq", "sr", "bs", "mk", "is", "ms", "th",
    "vi", "id", "he", "fa", "ur", "bn", "ta", "te", "ml", "ka",
    "auto",  # allow "auto" for auto-detect
}

VALID_DOMAINS: set[str] = {
    "general", "tehnic", "technical", "auto", "juridic", "legal",
    "medical", "financiar", "financial", "IT", "it",
    "constructii", "construction", "ITP", "itp",
}


def _validate_lang_code(code: str, field_name: str) -> str:
    """Validate and normalize a language code."""
    code = code.strip().lower()
    if code not in VALID_LANG_CODES:
        raise ValueError(
            f"{field_name}: '{code}' nu este un cod de limba ISO 639-1 valid. "
            f"Exemple valide: en, ro, de, fr, es, it"
        )
    return code


def _validate_domain(domain: str) -> str:
    """Validate glossary/TM domain."""
    domain = domain.strip()
    if domain and domain.lower() not in {d.lower() for d in VALID_DOMAINS}:
        raise ValueError(
            f"Domeniu invalid: '{domain}'. "
            f"Domenii valide: {', '.join(sorted(VALID_DOMAINS - {'auto'}))}"
        )
    return domain


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class TranslateTextRequest(BaseModel):
    text: str = Field(..., max_length=50000)
    source_lang: str = "en"
    target_lang: str = "ro"
    provider: str = "auto"
    use_tm: bool = True
    use_glossary: bool = True
    domain: str = "general"
    auto_tm: bool = True

    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        return _validate_lang_code(v, "source_lang/target_lang")

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        return _validate_domain(v)


class DetectRequest(BaseModel):
    text: str


class TMAddRequest(BaseModel):
    source: str
    target: str
    source_lang: str = "en"
    target_lang: str = "ro"
    domain: str = "general"

    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        return _validate_lang_code(v, "source_lang/target_lang")

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        return _validate_domain(v)


class GlossaryAddRequest(BaseModel):
    source: str
    target: str
    source_lang: str = "en"
    target_lang: str = "ro"
    domain: str = "general"
    notes: str | None = None
    client_id: int | None = None

    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        return _validate_lang_code(v, "source_lang/target_lang")

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        return _validate_domain(v)


class GlossaryUpdateRequest(BaseModel):
    source: str | None = None
    target: str | None = None
    source_lang: str | None = None
    target_lang: str | None = None
    domain: str | None = None
    notes: str | None = None
    client_id: int | None = None

    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        if v is not None:
            return _validate_lang_code(v, "source_lang/target_lang")
        return v

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        if v is not None:
            return _validate_domain(v)
        return v


class CompareRequest(BaseModel):
    text: str = Field(..., max_length=50000)
    source_lang: str = "en"
    target_lang: str = "ro"
    provider_a: str = Field(..., description="Primul provider (ex: deepl, azure, google)")
    provider_b: str = Field(..., description="Al doilea provider (ex: deepl, azure, google)")

    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        return _validate_lang_code(v, "source_lang/target_lang")


class QualityCheckRequest(BaseModel):
    source_text: str
    translated_text: str
    source_lang: str = "en"
    target_lang: str = "ro"

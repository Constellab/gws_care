"""LanguageState — manages the current user's display language preference."""

import reflex as rx
from gws_reflex_main import ReflexMainState

from .translations import get_translations


class LanguageState(ReflexMainState):
    """Stores and persists the display language for the current user.

    Exposes :attr:`tr` — a reactive dict of translated strings that components
    can access as ``LanguageState.tr["key"]``.
    """

    language: str = "fr"

    @rx.event
    async def on_load(self):
        await self._load_language()

    @rx.event
    async def set_language(self, lang: str | list[str]):
        if isinstance(lang, list):
            lang = lang[0] if lang else "en"
        self.language = lang
        await self._save_language(lang)

    @rx.var
    def tr(self) -> dict[str, str]:
        """Reactive translation dict for the current language."""
        return get_translations(self.language)

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _load_language(self) -> None:
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.user.user_language_pref import UserLanguagePref
                pref = UserLanguagePref.get_or_none(
                    UserLanguagePref.user_id == str(auth_user.id)
                )
                if pref:
                    self.language = pref.language
        except Exception as exc:
            pass

    async def _save_language(self, lang: str) -> None:
        try:
            with await self.authenticate_user() as auth_user:
                from gws_care.user.user_language_pref import UserLanguagePref
                pref, _ = UserLanguagePref.get_or_create(
                    user_id=str(auth_user.id)
                )
                pref.language = lang
                pref.save()
        except Exception as exc:
            pass

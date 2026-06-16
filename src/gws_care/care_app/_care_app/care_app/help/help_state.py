"""State for the help center page."""

import reflex as rx

from .help_articles import ARTICLES, HelpArticleDTO


class HelpState(rx.State):
    search_query: str = ""
    selected_article_id: str = ""

    def set_search(self, value: str) -> None:
        self.search_query = value

    def select_article(self, article_id: str) -> None:
        self.selected_article_id = article_id

    def close_article(self) -> None:
        self.selected_article_id = ""

    @rx.var
    def filtered_articles(self) -> list[HelpArticleDTO]:
        q = self.search_query.lower().strip()
        if not q:
            return ARTICLES
        return [
            a for a in ARTICLES
            if q in a.title.lower()
            or q in a.short_description.lower()
            or any(q in tag.lower() for tag in a.tags)
        ]

    @rx.var
    def selected_article(self) -> HelpArticleDTO:
        for a in ARTICLES:
            if a.id == self.selected_article_id:
                return a
        return HelpArticleDTO(
            id="", title="", short_description="", icon="circle-help",
            tags=[], roles=[], sections=[],
        )

    @rx.var
    def has_selected(self) -> bool:
        return bool(self.selected_article_id)

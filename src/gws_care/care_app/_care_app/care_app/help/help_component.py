"""Help center page — search bar, article card grid, and inline detail view."""

import reflex as rx
from gws_reflex_main import main_component

from ..common.page_layout import page_layout
from .help_articles import HelpArticleDTO, HelpSectionDTO
from .help_state import HelpState


# ── Role badge ────────────────────────────────────────────────────────────────

def _role_badge(role: rx.Var) -> rx.Component:
    return rx.badge(
        role,
        color_scheme=rx.match(
            role,
            ("Admin", "tomato"),
            ("Médecin", "blue"),
            ("Opérateur", "green"),
            ("Patient", "purple"),
            ("Responsable de compte", "orange"),
            "gray",
        ),
        variant="soft",
        size="1",
    )


# ── Article card (grid view) ──────────────────────────────────────────────────

def _article_card(article: HelpArticleDTO) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(article.icon, size=20, color="var(--accent-9)", flex_shrink="0"),
                rx.spacer(),
                rx.hstack(
                    rx.foreach(article.roles, _role_badge),
                    spacing="1",
                    wrap="wrap",
                    justify="end",
                ),
                width="100%",
                align="start",
            ),
            rx.text(
                article.title,
                size="3",
                weight="bold",
                color="var(--gray-12)",
            ),
            rx.text(
                article.short_description,
                size="2",
                color="var(--gray-9)",
                line_height="1.45em",
            ),
            spacing="2",
            width="100%",
            align_items="start",
        ),
        padding="1rem",
        border_radius="var(--radius-3)",
        border="1px solid var(--gray-5)",
        cursor="pointer",
        _hover={"border_color": "var(--accent-7)", "background": "var(--accent-2)"},
        on_click=lambda: HelpState.select_article(article.id),
        width="100%",
        min_height="130px",
        style={"transition": "border-color 0.12s ease, background 0.12s ease"},
    )


# ── Section block (detail view) ───────────────────────────────────────────────

def _section_block(section: HelpSectionDTO) -> rx.Component:
    return rx.vstack(
        rx.text(section.heading, size="3", weight="bold", color="var(--gray-12)"),
        rx.text(
            section.content,
            size="2",
            color="var(--gray-11)",
            line_height="1.65em",
            white_space="pre-line",
        ),
        spacing="1",
        width="100%",
        align_items="start",
    )


# ── Article detail view ───────────────────────────────────────────────────────

def _article_detail() -> rx.Component:
    article = HelpState.selected_article
    return rx.vstack(
        # Back button + title row
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=14),
                "Retour",
                variant="ghost",
                color_scheme="gray",
                size="2",
                on_click=HelpState.close_article,
                cursor="pointer",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        rx.hstack(
            rx.icon(article.icon, size=26, color="var(--accent-9)", flex_shrink="0"),
            rx.heading(article.title, size="5"),
            spacing="3",
            align="center",
        ),
        # Role badges
        rx.hstack(
            rx.foreach(article.roles, _role_badge),
            spacing="2",
            wrap="wrap",
        ),
        rx.separator(width="100%"),
        # Short description
        rx.text(
            article.short_description,
            size="3",
            color="var(--gray-10)",
            line_height="1.6em",
            font_style="italic",
        ),
        rx.separator(width="100%"),
        # Content sections
        rx.vstack(
            rx.foreach(article.sections, _section_block),
            spacing="4",
            width="100%",
            align_items="start",
        ),
        spacing="4",
        width="100%",
        max_width="760px",
        align_items="start",
        padding_bottom="2rem",
    )


# ── Empty search result ───────────────────────────────────────────────────────

def _empty_search() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon("search-x", size=40, color="var(--gray-6)"),
            rx.text("Aucun article trouvé", size="3", color="var(--gray-9)"),
            rx.text(
                "Essayez un autre mot-clé.",
                size="2",
                color="var(--gray-8)",
            ),
            spacing="2",
            align="center",
        ),
        padding="4rem",
        border="1px dashed var(--gray-5)",
        border_radius="8px",
        width="100%",
    )


# ── Help page ─────────────────────────────────────────────────────────────────

def help_page() -> rx.Component:
    return main_component(
        page_layout(
            rx.vstack(
                # Page header
                rx.hstack(
                    rx.icon("circle-help", size=24, color="var(--accent-9)"),
                    rx.heading("Centre d'aide", size="6"),
                    spacing="3",
                    align="center",
                ),
                rx.text(
                    "Recherchez une fonctionnalité ou parcourez les articles ci-dessous.",
                    size="2",
                    color="var(--gray-9)",
                ),
                # Search bar (always visible)
                rx.el.input(
                    placeholder="Rechercher une fonctionnalité…",
                    value=HelpState.search_query,
                    on_change=HelpState.set_search,
                    style={
                        "width": "100%",
                        "max_width": "560px",
                        "padding": "0.55rem 0.9rem",
                        "border": "1px solid var(--gray-6)",
                        "border_radius": "var(--radius-2)",
                        "font_size": "var(--font-size-2)",
                        "outline": "none",
                        "background": "var(--gray-1)",
                        "color": "var(--gray-12)",
                    },
                ),
                # Grid or detail view
                rx.cond(
                    HelpState.has_selected,
                    _article_detail(),
                    rx.cond(
                        HelpState.filtered_articles.length() > 0,
                        rx.grid(
                            rx.foreach(HelpState.filtered_articles, _article_card),
                            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                            spacing="4",
                            width="100%",
                        ),
                        _empty_search(),
                    ),
                ),
                spacing="4",
                width="100%",
                align_items="start",
            ),
        ),
    )

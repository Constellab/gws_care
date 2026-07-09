"""Shared reusable components: address autocomplete (IGN) + phone dial-code input.

Usage:
    from ..common.shared_address_phone_components import address_section, phone_input_field

    address_section(MyFormState)
    phone_input_field(MyFormState)

Required state interface (both vars and events must exist on the state class):
    Vars:
        form_country, country_filter, filtered_countries, show_country_suggestions,
        form_address, address_suggestions, show_address_suggestions, address_manual_mode,
        is_fetching_suggestions, form_postal_code, form_city, form_address_complement,
        form_phone_dial_code, form_phone, dial_code_options
    Events:
        set_country_filter, select_country_suggestion, close_autocomplete_dropdowns,
        fetch_address_suggestions, select_address_suggestion, toggle_address_manual_mode,
        set_form_postal_code, set_form_city, set_form_address_complement,
        set_form_phone_dial_code, set_form_phone
"""

import reflex as rx

from .language_state import LanguageState


def _field(label: str, input_component: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium"),
        input_component,
        width="100%",
        spacing="1",
    )


def _country_suggestion_item(country: str, state_cls) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("globe", size=12, color="var(--accent-9)"),
            rx.text(country, size="2"),
            spacing="2",
            align="center",
        ),
        padding="0.4rem 0.75rem",
        cursor="pointer",
        _hover={"background": "var(--accent-2)"},
        on_mouse_down=lambda: state_cls.select_country_suggestion(country),
        width="100%",
    )


def _address_suggestion_item(s, state_cls) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("map-pin", size=13, color="var(--accent-9)"),
            rx.text(s.fulltext, size="2"),
            spacing="2",
            align="center",
        ),
        padding="0.4rem 0.75rem",
        cursor="pointer",
        _hover={"background": "var(--accent-2)"},
        on_mouse_down=lambda: state_cls.select_address_suggestion(s.street, s.zip_code, s.city),
        width="100%",
    )


def address_section(state_cls, include_complement: bool = True) -> rx.Component:
    """Full address block: country autocomplete + street (IGN/manual) + complement + postal + city."""

    # ── Click-outside overlay — closes both dropdowns ─────────────────────────
    overlay = rx.cond(
        state_cls.show_country_suggestions,
        rx.box(
            position="fixed",
            top="0", left="0", right="0", bottom="0",
            z_index="49",
            background="transparent",
            on_click=state_cls.close_autocomplete_dropdowns,
        ),
        rx.cond(
            state_cls.show_address_suggestions,
            rx.box(
                position="fixed",
                top="0", left="0", right="0", bottom="0",
                z_index="49",
                background="transparent",
                on_click=state_cls.close_autocomplete_dropdowns,
            ),
            rx.fragment(),
        ),
    )

    # ── Country autocomplete ───────────────────────────────────────────────────
    country_input = _field(
        LanguageState.tr["field_country"],
        rx.box(
            rx.input(
                value=state_cls.country_filter,
                on_change=state_cls.set_country_filter,
                placeholder="Type a country…",
                size="2",
                width="100%",
            ),
            rx.cond(
                state_cls.show_country_suggestions,
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            state_cls.filtered_countries,
                            lambda c: _country_suggestion_item(c, state_cls),
                        ),
                        spacing="0",
                        width="100%",
                    ),
                    position="absolute",
                    top="100%",
                    left="0",
                    right="0",
                    background="white",
                    border="1px solid var(--gray-5)",
                    border_radius="var(--radius-2)",
                    box_shadow="0 4px 12px var(--gray-a5)",
                    z_index="100",
                    max_height="220px",
                    overflow_y="auto",
                ),
            ),
            position="relative",
            width="100%",
        ),
    )

    # ── Street: IGN autocomplete for France, plain input otherwise ─────────────
    street_label = rx.hstack(
        rx.text(LanguageState.tr["field_street_address"], size="2", weight="medium"),
        rx.cond(
            state_cls.form_country == "France",
            rx.cond(
                state_cls.address_manual_mode,
                rx.badge(
                    rx.icon("pencil", size=10),
                    " Manual entry",
                    color_scheme="orange",
                    variant="soft",
                    size="1",
                    cursor="pointer",
                    on_click=state_cls.toggle_address_manual_mode,
                ),
                rx.badge(
                    rx.icon("zap", size=10),
                    " IGN Autocomplete",
                    color_scheme="blue",
                    variant="soft",
                    size="1",
                    cursor="pointer",
                    on_click=state_cls.toggle_address_manual_mode,
                ),
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
        width="100%",
    )

    france_street = rx.vstack(
        street_label,
        rx.box(
            rx.input(
                value=state_cls.form_address,
                on_change=state_cls.fetch_address_suggestions,
                placeholder="8 boulevard de la Paix…",
                size="2",
                width="100%",
            ),
            rx.cond(
                state_cls.show_address_suggestions,
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            state_cls.address_suggestions,
                            lambda s: _address_suggestion_item(s, state_cls),
                        ),
                        spacing="0",
                        width="100%",
                    ),
                    position="absolute",
                    top="100%",
                    left="0",
                    right="0",
                    background="white",
                    border="1px solid var(--gray-5)",
                    border_radius="var(--radius-2)",
                    box_shadow="0 4px 12px var(--gray-a5)",
                    z_index="100",
                    max_height="220px",
                    overflow_y="auto",
                ),
            ),
            position="relative",
            width="100%",
        ),
        spacing="1",
        width="100%",
    )

    manual_street = rx.vstack(
        street_label,
        rx.input(
            value=state_cls.form_address,
            on_change=state_cls.set_form_address,
            placeholder="8 boulevard de la Paix…",
            size="2",
            width="100%",
        ),
        spacing="1",
        width="100%",
    )

    # Nested cond: France? → check manual mode; otherwise → plain
    street_field = rx.cond(
        state_cls.form_country == "France",
        rx.cond(
            state_cls.address_manual_mode,
            manual_street,
            france_street,
        ),
        manual_street,
    )

    postal_city = rx.grid(
        _field(
            LanguageState.tr["field_postal_code"],
            rx.input(
                value=state_cls.form_postal_code,
                on_change=state_cls.set_form_postal_code,
                placeholder="75001",
                size="2",
                width="100%",
            ),
        ),
        _field(
            LanguageState.tr["field_city"],
            rx.input(
                value=state_cls.form_city,
                on_change=state_cls.set_form_city,
                placeholder=LanguageState.tr["placeholder_city"],
                size="2",
                width="100%",
            ),
        ),
        columns="2",
        spacing="3",
        width="100%",
    )

    children = [
        overlay,
        rx.separator(width="100%"),
        rx.text(LanguageState.tr["section_address"], size="2", weight="bold", color="var(--gray-9)"),
        country_input,
        street_field,
    ]
    if include_complement:
        complement = _field(
            LanguageState.tr["field_address_complement"],
            rx.input(
                value=state_cls.form_address_complement,
                on_change=state_cls.set_form_address_complement,
                placeholder="Building A, apartment 12…",
                size="2",
                width="100%",
            ),
        )
        children.append(complement)
    children.append(postal_city)

    return rx.vstack(*children, width="100%", spacing="3")


def _dial_code_item(opt, state_cls) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(opt.flag, size="2"),
            rx.text(opt.code, size="2", weight="medium", min_width="3em"),
            rx.text(opt.name, size="2", color="var(--gray-9)"),
            spacing="2",
            align="center",
        ),
        padding="0.4rem 0.75rem",
        cursor="pointer",
        _hover={"background": "var(--accent-2)"},
        on_mouse_down=lambda: state_cls.select_dial_code_option(opt.code, opt.flag),
        width="100%",
    )


def phone_input_field(state_cls) -> rx.Component:
    """Phone: searchable combobox (type to filter all countries) + number input."""
    overlay = rx.cond(
        state_cls.show_dial_code_suggestions,
        rx.box(
            position="fixed", top="0", left="0", right="0", bottom="0",
            z_index="49", background="transparent",
            on_click=state_cls.close_dial_code_suggestions,
        ),
        rx.fragment(),
    )
    return _field(
        LanguageState.tr["field_phone"],
        rx.box(
            overlay,
            rx.hstack(
                rx.box(
                    rx.input(
                        value=state_cls.dial_code_filter,
                        on_change=state_cls.set_dial_code_filter,
                        placeholder="🇫🇷 +33",
                        size="2",
                        width="140px",
                    ),
                    rx.cond(
                        state_cls.show_dial_code_suggestions,
                        rx.box(
                            rx.vstack(
                                rx.foreach(
                                    state_cls.filtered_dial_codes,
                                    lambda opt: _dial_code_item(opt, state_cls),
                                ),
                                spacing="0",
                                width="100%",
                            ),
                            position="absolute",
                            top="100%",
                            left="0",
                            background="white",
                            border="1px solid var(--gray-5)",
                            border_radius="var(--radius-2)",
                            box_shadow="0 4px 12px var(--gray-a5)",
                            z_index="100",
                            max_height="220px",
                            overflow_y="auto",
                            min_width="280px",
                        ),
                    ),
                    position="relative",
                ),
                rx.input(
                    value=state_cls.form_phone,
                    on_change=state_cls.set_form_phone,
                    placeholder="6 00 00 00 00",
                    size="2",
                    flex="1",
                    min_width="0",
                ),
                spacing="2",
                width="100%",
                align="center",
            ),
            width="100%",
        ),
    )

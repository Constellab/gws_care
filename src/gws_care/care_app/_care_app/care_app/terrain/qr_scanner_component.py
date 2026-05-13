"""Python wrapper for the camera-based QR scanner JSX component.

The JSX file (qr_scanner.jsx) must live alongside this Python file so that
`rx.asset("qr_scanner.jsx", shared=True)` can locate it at import time.

Usage in a component function:
    qr_scanner_component(
        active=TerrainState.scanner_active,
        on_scan=TerrainState.on_scan_detected,
        on_error=TerrainState.on_scan_error,
    )
"""
import reflex as rx
from reflex import event

# Load jsQR from the local assets (placed in care_app assets/jsQR.min.js).
_jsqr_script_src = "/jsQR.min.js"

# Register the JSX asset so Reflex copies it to .web/public/
_asset_path = rx.asset("qr_scanner.jsx", shared=True)
_component_js_path = "$/public/" + _asset_path


class QrScannerComponent(rx.Component):
    """Camera-based QR scanner component.

    Attributes:
        active: Whether the camera should be running and scanning.
        on_scan: Event handler called with the decoded QR string (str arg).
        on_error: Event handler called with an error message string (str arg).
    """

    library: str = _component_js_path
    tag: str = "QrScannerComponent"

    # Props
    active: rx.Var[bool] = False

    # Event handlers — passthrough passes the raw JS argument as a positional arg
    on_scan: rx.EventHandler[event.passthrough_event_spec(str)]
    on_error: rx.EventHandler[event.passthrough_event_spec(str)]


def qr_scanner_component(
    active: rx.Var[bool],
    on_scan,
    on_error,
    **props,
) -> rx.Component:
    """Render the camera QR scanner with the jsQR script loaded."""
    return rx.fragment(
        # Load jsQR library before the component needs it
        rx.script(src=_jsqr_script_src),
        QrScannerComponent.create(
            active=active,
            on_scan=on_scan,
            on_error=on_error,
            **props,
        ),
    )

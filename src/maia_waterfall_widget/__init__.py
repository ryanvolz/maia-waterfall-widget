import importlib.metadata
import pathlib

import anywidget
import numpy as np
import traitlets

_DEV = True  # switch to False for production

try:
    __version__ = importlib.metadata.version("maia_waterfall_widget")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

if _DEV:
    # from `npx vite`
    ESM = "http://localhost:5173/js/widget.js?anywidget"
    CSS = ""
else:
    # from `npx vite build`
    bundled_assets_dir = pathlib.Path(__file__).parent / "static"
    ESM = (bundled_assets_dir / "widget.js").read_text()
    CSS = (bundled_assets_dir / "widget.css").read_text()


class Widget(anywidget.AnyWidget):
    _esm = ESM
    _css = CSS
    center_freq_hz = traitlets.Float(915e6).tag(sync=True)
    colormap = traitlets.Enum(
        values={"turbo", "viridis", "inferno"},
        default_value="turbo",
    ).tag(sync=True)
    sample_rate_hz = traitlets.Float(960e3).tag(sync=True)
    spectrum_visible = traitlets.Bool(False).tag(sync=True)
    waterfall_max_db = traitlets.Float(95.0).tag(sync=True)
    waterfall_min_db = traitlets.Float(25.0).tag(sync=True)
    waterfall_update_rate_hz = traitlets.Float(29.296875).tag(sync=True)
    waterfall_visible = traitlets.Bool(True).tag(sync=True)

    def put_spectrum(
        self, linear_spectrum: np.ndarray[tuple[int | int, int], np.dtype[np.generic]]
    ):
        spec_f32 = np.ascontiguousarray(linear_spectrum, dtype=np.float32)
        if len(spec_f32.shape) == 1:
            buffers = [spec_f32]
        else:
            buffers = [s for s in spec_f32]
        self.send("put_spectrum", buffers=buffers)

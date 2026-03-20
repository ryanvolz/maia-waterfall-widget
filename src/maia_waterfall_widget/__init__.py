import dataclasses
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


@dataclasses.dataclass
class WaterfallShape:
    time: int = 512
    """Number of time samples (height)"""
    freq: int = 4096
    """Number of frequency samples (width)"""


class Waterfall(anywidget.AnyWidget):
    _esm = ESM
    _css = CSS

    # Prefix these with _ and force them to be supplied in __init__
    # because they are intended to be static:
    # they are needed to initialize the model but after creation
    # the JS side will not observe for changes since it can't
    # support changing the waterfall shape.
    _num_freq_samples = traitlets.Int(4096).tag(sync=True)
    _num_time_samples = traitlets.Int(512).tag(sync=True)

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

    def __init__(
        self, waterfall_shape: WaterfallShape | tuple[int, int], *args, **kwargs
    ):
        """Create a Waterfall widget with a given shape.

        Parameters
        ----------
        waterfall_shape : WaterfallShape | tuple[int, int]
            Waterfall shape in number of time samples (height) by
            number of frequency samples (width): (n_time, n_freq).

        """
        super().__init__(*args, **kwargs)
        if not isinstance(waterfall_shape, WaterfallShape):
            waterfall_shape = WaterfallShape(*waterfall_shape)
        self.shape = waterfall_shape
        self._num_freq_samples = waterfall_shape.freq
        self._num_time_samples = waterfall_shape.time

    def put_spectrum(
        self, linear_spectrum: np.ndarray[tuple[int | int, int], np.dtype[np.generic]]
    ):
        """Add a spectrum line or lines to the waterfall display.

        This is not universally supported because not all
        implementers of the Anywidget Front-End Module support
        `send` (e.g. NiceGUI) or they might not support the
        `buffers` argument of `send`.
        See https://github.com/manzt/anywidget/issues/932.

        Parameters
        ----------
        linear_spectrum : np.ndarray[tuple[int | int, int], np.dtype[np.generic]]
            One-dimensional array of length `waterfall_shape[1]`
            containing a line of spectral power to add to the
            waterfall display, or a two-dimensional array of
            multiple such spectra. The array must give the
            linear power and will subsequently be converted
            to decibels for display. Note that all values will
            be converted to 32-bit floating point.

        """
        if linear_spectrum.shape[-1] != self._num_freq_samples:
            msg = f"Spectrum size must match configured {self._num_freq_samples=}"
            raise ValueError(msg)
        spec_f32 = np.ascontiguousarray(linear_spectrum, dtype=np.float32)
        if len(spec_f32.shape) == 1:
            buffers = [spec_f32]
        else:
            buffers = [s for s in spec_f32]
        self.send("put_spectrum", buffers=buffers)

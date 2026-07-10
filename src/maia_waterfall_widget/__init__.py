import dataclasses
import importlib.metadata
import json
import pathlib
import socket

import anywidget
import numpy as np
import traitlets

try:
    __version__ = importlib.metadata.version("maia_waterfall_widget")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


try:
    vite_live_esm = is_port_in_use("localhost", 5173)
except Exception:
    vite_live_esm = False

if vite_live_esm:
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

    colormap = traitlets.Enum(
        values={"turbo", "viridis", "inferno"},
        default_value="turbo",
    ).tag(sync=True)
    freq_samprate_hz = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=(0.0, 10e6)
    ).tag(sync=True)
    mqtt_topic = traitlets.Unicode("").tag(sync=True)
    mqtt_url = traitlets.Unicode("").tag(sync=True)
    spectrum_visible = traitlets.Bool(False).tag(sync=True)
    subchannel_idx = traitlets.Int(0).tag(sync=True)
    waterfall_max_db = traitlets.Float(0.0).tag(sync=True)
    waterfall_min_db = traitlets.Float(-70.0).tag(sync=True)
    waterfall_update_rate_hz = traitlets.Float(None, allow_none=True).tag(sync=True)
    waterfall_visible = traitlets.Bool(True).tag(sync=True)

    def __init__(
        self, waterfall_shape: WaterfallShape | tuple[int, int], *args, **kwargs
    ):
        """Create a Waterfall widget with a given shape.

        Parameters
        ----------
        waterfall_shape : WaterfallShape | tuple[int, int]
            Waterfall shape in visible number of time samples
            (height) by number of frequency samples (width):
            (n_time, n_freq).
            [Note: the internal texture will hold twice the
             number of time samples to enable the scrolling
             animation.]

        """
        super().__init__(*args, **kwargs)
        if not isinstance(waterfall_shape, WaterfallShape):
            waterfall_shape = WaterfallShape(*waterfall_shape)
        self.waterfall_shape = waterfall_shape
        self._num_freq_samples = waterfall_shape.freq
        self._num_time_samples = waterfall_shape.time

    @property
    def center_freq_hz(self):
        return self.freq_samprate_hz[0]

    @center_freq_hz.setter
    def center_freq_hz(self, new_center_freq_hz: float):
        self.freq_samprate_hz = (new_center_freq_hz, self.freq_samprate_hz[1])

    @property
    def sample_rate_hz(self):
        return self.freq_samprate_hz[1]

    @sample_rate_hz.setter
    def sample_rate_hz(self, new_sample_rate_hz: float):
        self.freq_samprate_hz = (self.freq_samprate_hz[0], new_sample_rate_hz)

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
        spec_f32 = np.ascontiguousarray(linear_spectrum, dtype=np.float32)
        if len(spec_f32.shape) == 1:
            buffers = [spec_f32]
        else:
            buffers = [s for s in spec_f32]
        self.send("put_spectrum", buffers=buffers)

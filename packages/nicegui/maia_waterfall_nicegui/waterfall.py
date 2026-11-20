import base64
import inspect
import typing

import numpy as np
from nicegui import binding, ui


class Waterfall(ui.element, component="components/waterfall.js"):
    averaging_count = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("averaging-count", value)
    )
    colormap = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("colormap", value)
    )
    max_db = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("max-db", value)
    )
    min_db = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("min-db", value)
    )
    num_freq_samples = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("num-freq-samples", value)
    )
    num_time_samples = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("num-time-samples", value)
    )
    spectrum_visible = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("spectrum-visible", value)
    )
    toolbar_height = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("toolbar-height", value)
    )
    waterfall_visible = binding.BindableProperty(
        on_change=lambda sender, value: typing.cast(
            typing.Self, sender
        )._handle_attr_change("waterfall-visible", value)
    )

    def __init__(
        self,
        num_freq_samples: int = 4096,
        num_time_samples: int = 512,
        *,
        waterfall_visible: bool = True,
        **kwargs,
    ) -> None:
        super().__init__()
        self._center_freq_hz = None
        self._sample_rate_hz = None
        self._spectrum_rate_hz = None
        # set event handlers and default values for descriptor attributes defined above
        # (initial values can be provided as __init__ arguments)
        for attr, obj in inspect.getmembers_static(self):
            if isinstance(obj, binding.BindableProperty):
                attr_prop = attr.replace("_", "-")
                self.on(
                    f"update:{attr_prop}",
                    lambda e, attr=attr: self._handle_client_attr_change(attr, e.args),
                )
                init_arg = kwargs.get(attr, locals().get(attr, None))
                setattr(self, attr, init_arg)
                self._props.set_optional(attr_prop, init_arg)

    def _handle_attr_change(self, attr_prop, value):
        print(f"Setting {attr_prop} to {value}")
        self._props[attr_prop] = value

    def _handle_client_attr_change(self, attr, value):
        # with self.props.suspend_updates():
        #     setattr(self, attr, value)
        setattr(self, attr, value)
        # setattr(self, "___" + attr, value)

    def bind_attr(
        self,
        attr,
        target_object,
        target_name="value",
        forward=None,
        backward=None,
        strict=None,
    ):
        binding.bind(
            self,
            attr,
            target_object,
            target_name,
            forward=forward,
            backward=backward,
            self_strict=False,
            other_strict=strict,
        )
        return self

    def bind_attr_from(
        self, attr, target_object, target_name="value", backward=None, strict=None
    ):
        binding.bind_from(
            self,
            attr,
            target_object,
            target_name,
            backward=backward,
            self_strict=False,
            other_strict=strict,
        )
        return self

    def bind_attr_to(
        self, attr, target_object, target_name="value", forward=None, strict=None
    ):
        binding.bind_to(
            self,
            attr,
            target_object,
            target_name,
            forward=forward,
            self_strict=False,
            other_strict=strict,
        )
        return self

    def bind_all_to(self, target_object, forward=None, strict=None):
        for attr, obj in inspect.getmembers_static(self):
            if isinstance(obj, binding.BindableProperty):
                self.bind_attr_to(
                    attr, target_object, attr, forward=forward, strict=strict
                )
        return self

    def update_from_props(self):
        self.run_method("update_from_props")

    def get(self, attr, default=None):
        return getattr(self, attr, default)

    def set(self, attr, value):
        """Set given attribute to `value` and update the client"""
        setattr(self, attr, value)
        self.update_from_props()
        return self

    def set_freq_samprate(
        self, center_freq_hz: float | None = None, sample_rate_hz: float | None = None
    ) -> None:
        """Set the frequency axis (center and bandwidth) of the waterfall display.

        Parameters
        ----------
        center_freq_hz : float | None
            Center frequency of the provided spectrum, in Hertz. This value will
            set the center of the displayed frequency axis. If None, the current
            value is maintained.

        sample_rate_hz : float | None
            Sample rate from which the spectrum was calculated, in Hertz. This value
            set the bandwidth of the displayed frequency axis. If None, the current
            value is maintained.

        """
        if center_freq_hz is None:
            center_freq_hz = self._center_freq_hz
        if sample_rate_hz is None:
            sample_rate_hz = self._sample_rate_hz
        if (center_freq_hz != self._center_freq_hz) or (
            sample_rate_hz != self._sample_rate_hz
        ):
            payload = {
                "center_freq_hz": center_freq_hz if not None else 0,
                "sample_rate_hz": sample_rate_hz if not None else 1000000,
            }
            self.run_method("set_freq_samprate", payload)
            self._center_freq_hz = center_freq_hz
            self._sample_rate_hz = sample_rate_hz

    def set_spectrum_rate(self, spectrum_rate_hz: float) -> None:
        """Set the rate at which spectra are drawn to the waterfall display.

        Parameters
        ----------
        spectrum_rate_hz : float | None
            Rate at which individual spectra are provided and should be displayed,
            in Hertz. If None, the current value is maintained.

        """
        if spectrum_rate_hz != self._spectrum_rate_hz:
            payload = {
                "spectrum_rate_hz": spectrum_rate_hz,
            }
            self.run_method("set_spectrum_rate", payload)
            self._spectrum_rate_hz = spectrum_rate_hz

    def put_spectrum(
        self,
        linear_spectrum: np.ndarray[tuple[int, int], np.dtype[np.generic]],
        spectrum_rate_hz: float | None = None,
        center_freq_hz: float | None = None,
        sample_rate_hz: float | None = None,
    ):
        """Add a spectrum line or lines to the waterfall display.

        Parameters
        ----------
        linear_spectrum : np.ndarray[tuple[int | int, int], np.dtype[np.generic]]
            One-dimensional array containing a line of spectral power to add to the
            waterfall display, or a two-dimensional array of multiple such spectra.
            The array must give the linear power and will subsequently be converted
            to decibels for display. Note that all values will be converted to
            32-bit floating point.

        spectrum_rate_hz : float | None
            Rate at which individual spectra are provided and should be displayed,
            in Hertz. If None, the current value is maintained.

        center_freq_hz : float | None
            Center frequency of the provided spectrum, in Hertz. This value will
            set the center of the displayed frequency axis. If None, the current
            value is maintained.

        sample_rate_hz : float | None
            Sample rate from which the spectrum was calculated, in Hertz. This value
            set the bandwidth of the displayed frequency axis. If None, the current
            value is maintained.

        """
        if spectrum_rate_hz is not None:
            self.set_spectrum_rate(spectrum_rate_hz)
        self.set_freq_samprate(
            center_freq_hz=center_freq_hz, sample_rate_hz=sample_rate_hz
        )
        spec_f32 = np.ascontiguousarray(linear_spectrum, dtype="<f4")
        if len(spec_f32.shape) == 1:
            spectra = [spec_f32]
        else:
            spectra = [s for s in spec_f32]
        for spec in spectra:
            payload = {
                "data": base64.b64encode(spec.tobytes(order="C")).decode(),
                "dtype": "<float32",
                "shape": spec.shape,
            }
            self.run_method("put_spectrum", payload)

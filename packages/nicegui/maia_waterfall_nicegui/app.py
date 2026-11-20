import asyncio
import queue

import numpy as np
from nicegui import app, background_tasks, native, ui

from maia_waterfall_nicegui import Waterfall


class PlayWaterfallButton(ui.button):
    def __init__(self, *args, icon="play_arrow", **kwargs) -> None:
        self._task_queue = queue.Queue(1)
        super().__init__(*args, icon="play_arrow", **kwargs)
        self.on("click", self.toggle)
        self.toggle()

    def toggle(self):
        if not self._task_queue.full():
            self._task_queue.put(
                background_tasks.create(play_spectra(self.parent_slot.parent))
            )
        else:
            self._task_queue.get().cancel()
        self.update()

    def update(self):
        if not self._task_queue.full():
            with self.props.suspend_updates():
                self.props("icon=play_arrow")
        else:
            with self.props.suspend_updates():
                self.props("icon=pause")
        super().update()

    def __del__(self):
        if self._task_queue.full():
            self._task_queue.get().cancel()


@ui.page("/")
def root() -> None:
    ui.query(".nicegui-content").classes("p-0").style(
        "min-height: inherit; max-height: 0px"
    )

    if "waterfall" not in app.storage.user:
        app.storage.user["waterfall"] = {
            "num_freq_samples": 2048,
            "num_time_samples": 250,
        }

    @ui.refreshable
    def make_waterfall(num_freq_samples=None, num_time_samples=None):
        kwargs = app.storage.user["waterfall"]
        if num_freq_samples is not None:
            kwargs["num_freq_samples"] = num_freq_samples
        if num_time_samples is not None:
            kwargs["num_time_samples"] = num_time_samples
        with Waterfall(**kwargs).bind_all_to(
            app.storage.user["waterfall"]
        ) as waterfall:
            PlayWaterfallButton().props("dense round")
            ui.button(
                "Refresh",
                on_click=lambda e: make_waterfall.refresh(
                    num_freq_samples=waterfall.num_freq_samples,
                    num_time_samples=waterfall.num_time_samples,
                ),
            )
            ui.button(
                "Reload",
                on_click=ui.navigate.reload,
            )
        return waterfall

    waterfall = make_waterfall()
    print(waterfall.props)
    if len(app.storage.user["waterfall"].change_handlers) < 2:
        app.storage.user["waterfall"].on_change(lambda e: print(e.sender))
    background_tasks.create(test_change(waterfall))


async def test_change(waterfall):
    await asyncio.sleep(5)
    waterfall.spectrum_visible = not waterfall.spectrum_visible
    # waterfall.update_from_props()


async def play_spectra(waterfall) -> None:
    rng = np.random.default_rng()
    while not app.is_stopped:
        # await asyncio.sleep(1.0)
        # for n in range(10):
        #     waterfall.put_spectrum(
        #         rng.normal(scale=1e-1, size=2048) ** 2,
        #         spectrum_rate_hz=10,
        #         sample_rate_hz=10e6,
        #         center_freq_hz=None,
        #     )
        await asyncio.sleep(0.1)
        waterfall.put_spectrum(
            rng.normal(scale=1e-1, size=2048) ** 2,
            spectrum_rate_hz=10,
            sample_rate_hz=10e6,
            center_freq_hz=None,
        )


def main(reload=False):
    ui.run(
        port=native.find_open_port(),
        reload=reload,
        storage_secret="THIS_UUID_LACKS_ENTROPY",
        uvicorn_reload_includes="*.py,components/*.css,components/*.js",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main(reload=True)

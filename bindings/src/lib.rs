use maia_wasm::render::RenderEngine;
use maia_wasm::ui::colormap::Colormap;
use maia_wasm::waterfall::{Waterfall, WaterfallShape};
use std::{cell::RefCell, rc::Rc};
use wasm_bindgen::prelude::*;

fn colormap_from_string(colormap_str: &str) -> Result<Colormap, &str> {
    match colormap_str {
        "turbo" => Ok(Colormap::Turbo),
        "viridis" => Ok(Colormap::Viridis),
        "inferno" => Ok(Colormap::Inferno),
        _ => Err("invalid colormap name"),
    }
}

#[wasm_bindgen]
#[derive(Clone)]
pub struct WaterfallJsAPI {
    waterfall: Rc<RefCell<Waterfall>>,
    render_engine: Rc<RefCell<RenderEngine>>,
}

#[wasm_bindgen]
impl WaterfallJsAPI {
    #[wasm_bindgen(getter)]
    pub fn center_freq_hz(&self) -> f64 {
        self.waterfall.borrow().get_freq_samprate().0
    }
    #[wasm_bindgen(setter)]
    pub fn set_center_freq_hz(&self, value: f64) -> Result<(), JsValue> {
        let mut waterfall = self.waterfall.borrow_mut();
        let sample_rate_hz = waterfall.get_freq_samprate().1;
        waterfall.set_freq_samprate(
            value,
            sample_rate_hz,
            &mut self.render_engine.borrow_mut(),
        )?;
        Ok(())
    }

    #[wasm_bindgen]
    pub fn put_waterfall_spectrum(&mut self, spectrum_linear: &js_sys::Float32Array) {
        self.waterfall.borrow_mut().put_waterfall_spectrum(spectrum_linear);
    }

    #[wasm_bindgen(getter)]
    pub fn sample_rate_hz(&self) -> f64 {
        self.waterfall.borrow().get_freq_samprate().1
    }
    #[wasm_bindgen(setter)]
    pub fn set_sample_rate_hz(&self, value: f64) -> Result<(), JsValue> {
        let mut waterfall = self.waterfall.borrow_mut();
        let center_freq_hz = waterfall.get_freq_samprate().0;
        waterfall.set_freq_samprate(
            center_freq_hz,
            value,
            &mut self.render_engine.borrow_mut(),
        )?;
        Ok(())
    }

    #[wasm_bindgen]
    pub fn set_freq_samprate(
        &self,
        center_freq_hz: f64,
        sample_rate_hz: f64,
    ) -> Result<(), JsValue> {
        self.waterfall.borrow_mut().set_freq_samprate(
            center_freq_hz,
            sample_rate_hz, &mut self.render_engine.borrow_mut(),
        )?;
        Ok(())
    }

    #[wasm_bindgen(setter)]
    pub fn set_colormap(&self, value: &str) -> Result<(), JsValue> {
        let cmap = colormap_from_string(value)?;
        let mut render_engine = self.render_engine.borrow_mut();
        self.waterfall
            .borrow()
            .load_colormap(&mut render_engine, cmap.colormap_as_slice())
            .unwrap();
        Ok(())
    }

    #[wasm_bindgen(setter)]
    pub fn set_waterfall_max_db(&self, value: f32) {
        self.waterfall.borrow_mut().set_waterfall_max(value);
    }

    #[wasm_bindgen(setter)]
    pub fn set_waterfall_min_db(&self, value: f32) {
        self.waterfall.borrow_mut().set_waterfall_min(value);
    }

    #[wasm_bindgen(setter)]
    pub fn set_waterfall_update_rate_hz(&self, value: f32) {
        self.waterfall.borrow_mut().set_waterfall_update_rate(value);
    }

    #[wasm_bindgen(getter)]
    pub fn spectrum_visible(&self) -> bool {
        self.waterfall.borrow().is_spectrum_visible()
    }
    #[wasm_bindgen(setter)]
    pub fn set_spectrum_visible(&self, value: bool) {
        self.waterfall.borrow_mut().set_spectrum_visible(value);
    }

    #[wasm_bindgen(getter)]
    pub fn waterfall_visible(&self) -> bool {
        self.waterfall.borrow().is_waterfall_visible()
    }
    #[wasm_bindgen(setter)]
    pub fn set_waterfall_visible(&self, value: bool) {
        self.waterfall.borrow_mut().set_waterfall_visible(value);
    }
}

#[wasm_bindgen]
pub fn make_waterfall(
    canvas_id: &str,
    num_freq_samples: usize,
    num_time_samples: usize,
) -> Result<WaterfallJsAPI, JsValue> {
    let (window, document) = maia_wasm::get_window_and_document()?;
    let canvas = Rc::new(
        document
            .get_element_by_id(canvas_id)
            .ok_or(&format!("unable to get {canvas_id} canvas element"))?
            .dyn_into::<web_sys::HtmlCanvasElement>()?,
    );
    let (
        render_engine,
        waterfall,
        _,
    ) = maia_wasm::new_waterfall(
        &window,
        &document,
        &canvas,
        WaterfallShape {
            freq: num_freq_samples,
            time: num_time_samples,
        },
    )?;

    maia_wasm::setup_render_loop(render_engine.clone(), waterfall.clone());

    Ok(WaterfallJsAPI{waterfall: waterfall, render_engine: render_engine})
}

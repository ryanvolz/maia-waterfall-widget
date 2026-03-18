use maia_wasm::render::RenderEngine;
use maia_wasm::ui::colormap::Colormap;
use maia_wasm::waterfall::Waterfall;
use std::{cell::RefCell, rc::Rc};
use wasm_bindgen::prelude::*;

const NFFT: usize = 4096;

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
        self.waterfall.borrow_mut().get_freq_samprate().0
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

    #[wasm_bindgen(getter)]
    pub fn sample_rate_hz(&self) -> f64 {
        self.waterfall.borrow_mut().get_freq_samprate().1
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
        self.waterfall.borrow_mut().is_spectrum_visible()
    }
    #[wasm_bindgen(setter)]
    pub fn set_spectrum_visible(&self, value: bool) {
        self.waterfall.borrow_mut().set_spectrum_visible(value);
    }

    #[wasm_bindgen(getter)]
    pub fn waterfall_visible(&self) -> bool {
        self.waterfall.borrow_mut().is_waterfall_visible()
    }
    #[wasm_bindgen(setter)]
    pub fn set_waterfall_visible(&self, value: bool) {
        self.waterfall.borrow_mut().set_waterfall_visible(value);
    }
}

#[wasm_bindgen]
pub fn make_waterfall(canvas_id: &str) -> Result<WaterfallJsAPI, JsValue> {
    let (window, document) = maia_wasm::get_window_and_document()?;
    let canvas = Rc::new(
        document
            .get_element_by_id(canvas_id)
            .ok_or(&format!("unable to get {canvas_id} canvas element"))?
            .dyn_into::<web_sys::HtmlCanvasElement>()?,
    );
    let (render_engine, waterfall, _) = maia_wasm::new_waterfall(&window, &document, &canvas)?;

    Ok(WaterfallJsAPI{waterfall: waterfall, render_engine: render_engine})
}

#[wasm_bindgen]
pub fn generate_waterfall(waterfall_api: &WaterfallJsAPI) -> Result<(), JsValue> {
    let (window, _document) = maia_wasm::get_window_and_document()?;
    let mut generator = WaterfallGenerator::new();
    let handler = Closure::<dyn FnMut()>::new({
        let waterfall = Rc::clone(&waterfall_api.waterfall);
        move || {
            generator.put_line(&mut waterfall.borrow_mut());
        }
    });
    let interval_ms = 34;
    window.set_interval_with_callback_and_timeout_and_arguments_0(
        handler.into_js_value().unchecked_ref(),
        interval_ms,
    )?;

    maia_wasm::setup_render_loop(waterfall_api.render_engine.clone(), waterfall_api.waterfall.clone());
    Ok(())
}

// We generate waterfall lines by reading a JPEG file that is embedded in the wasm file

const WATERFALL_JPEG: &[u8; 888519] = include_bytes!("waterfall.jpg");
const WATERFALL_LINES: usize = 3955;

struct WaterfallGenerator {
    data: Box<[f32]>,
    current_line: usize,
}

impl WaterfallGenerator {
    fn new() -> WaterfallGenerator {
        let mut decoder = jpeg_decoder::Decoder::new(&WATERFALL_JPEG[..]);
        let pixels = decoder.decode().expect("failed to decode waterfall JPEG");
        let data = pixels
            .into_iter()
            .map(|x| {
                // Scale from 0-255 JPEG pixel data to dB units. The dB range in
                // the waterfall is 67.7 dB. The range in the JPEG is the full
                // 0-255 range. We arbitrarily set the minimum waterfall power
                // to 20 dB.
                let db = 67.7 * f32::from(x) / 255.0 + 20.0;
                // convert dB to linear power units
                10.0_f32.powf(0.1 * db)
            })
            .collect::<Vec<_>>()
            .into_boxed_slice();
        WaterfallGenerator {
            data,
            current_line: 0,
        }
    }

    fn put_line(&mut self, waterfall: &mut Waterfall) {
        let line = &self.data[NFFT * self.current_line..NFFT * (self.current_line + 1)];
        self.current_line += 1;
        if self.current_line == WATERFALL_LINES {
            self.current_line = 0;
        }
        // Safety: the view into self.data is always dropped before self.data
        unsafe {
            let line = js_sys::Float32Array::view(line);
            waterfall.put_waterfall_spectrum(&line);
        }
    }
}

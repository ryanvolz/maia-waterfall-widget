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

fn resample_spectrum(
    spectrum_linear: &js_sys::Float32Array,
    num_samples: usize,
) -> Result<js_sys::Float32Array, String> {
    // Fourier resampling a la scipy.signal.resample (without windowing)
    let n_x = spectrum_linear.length() as usize;

    if n_x == num_samples {
        return Ok(spectrum_linear.clone());
    }

    let mut planner = realfft::RealFftPlanner::<f32>::new();
    let rfft = planner.plan_fft_forward(n_x);
    let irfft = planner.plan_fft_inverse(num_samples);
    let mut x = spectrum_linear.to_vec();
    // common vec for referencing result of forward FFT and input to inverse FFT
    // using their corresponding complex output/input lengths
    let mut y_vec = if n_x > num_samples {
        rfft.make_output_vec()
    } else {
        // make_input_vec() initializes with zeros, so it will contain forward result
        // zero-padded for use in the inverse real FFT
        irfft.make_input_vec()
    };
    let mut x_r = irfft.make_output_vec();

    // first convert with ln so all reals are valid instead of just positive values
    // (and thus interpolate in the space on which the spectrum will be viewed)
    for el in x.iter_mut() {
        *el = el.ln();
    }

    match rfft.process(&mut x, &mut y_vec[..rfft.complex_len()]) {
        Err(ffterr) => return Err(ffterr.to_string()),
        Ok(val) => val,
    }
    // account for unpaired bin at m / 2
    let m = std::cmp::min(num_samples, n_x);
    if (m % 2) == 0 {
        if num_samples < n_x {
            // sample at bin m / 2 must also have imaginary part == 0 since it must
            // be its own complex conjugate to satisfy symmetry
            y_vec[m / 2] = y_vec[m / 2] + y_vec[m / 2].conj();
        } else {
            y_vec[m / 2] = 0.5 * y_vec[m / 2];
        }
    }
    // apply scaling (rfft/irfft do not apply any scaling)
    for el in y_vec[..irfft.complex_len()].iter_mut() {
        *el = *el / (n_x as f32);
    }
    match irfft.process(&mut y_vec[..irfft.complex_len()], &mut x_r) {
        Err(ffterr) => return Err(ffterr.to_string()),
        Ok(val) => val,
    }

    // convert back from reals to positive values by applying inverse of ln done above
    for el in x_r.iter_mut() {
        *el = el.exp();
    }

    Ok(js_sys::Float32Array::new_from_slice(&x_r))
}

#[wasm_bindgen]
#[derive(Clone)]
pub struct WaterfallJsAPI {
    waterfall: Rc<RefCell<Waterfall>>,
    render_engine: Rc<RefCell<RenderEngine>>,
    shape: WaterfallShape,
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
        waterfall.set_freq_samprate(value, sample_rate_hz, &mut self.render_engine.borrow_mut())?;
        Ok(())
    }

    #[wasm_bindgen]
    pub fn put_waterfall_spectrum(
        &mut self,
        spectrum_linear: &js_sys::Float32Array,
    ) -> Result<(), JsValue> {
        let resampled_spectrum_linear = resample_spectrum(spectrum_linear, self.shape.freq)?;
        self.waterfall
            .borrow_mut()
            .put_waterfall_spectrum(&resampled_spectrum_linear);
        Ok(())
    }

    #[wasm_bindgen]
    pub fn resize_canvas(&mut self) {
        self.render_engine.borrow_mut().resize_canvas().unwrap_or_default();
        self.waterfall
            .borrow_mut()
            .resize_canvas(&mut self.render_engine.borrow_mut()).unwrap_or_default();
    }

    #[wasm_bindgen(getter)]
    pub fn sample_rate_hz(&self) -> f64 {
        self.waterfall.borrow().get_freq_samprate().1
    }
    #[wasm_bindgen(setter)]
    pub fn set_sample_rate_hz(&self, value: f64) -> Result<(), JsValue> {
        let mut waterfall = self.waterfall.borrow_mut();
        let center_freq_hz = waterfall.get_freq_samprate().0;
        waterfall.set_freq_samprate(center_freq_hz, value, &mut self.render_engine.borrow_mut())?;
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
            sample_rate_hz,
            &mut self.render_engine.borrow_mut(),
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
    // WaterfallShape specifies the texture size, which requires twice
    // the number of visible time samples to enable animated scrolling
    let shape = WaterfallShape {
        freq: num_freq_samples,
        time: 2 * num_time_samples,
    };
    let (render_engine, waterfall, _) =
        maia_wasm::new_waterfall(&window, &document, &canvas, shape)?;

    maia_wasm::setup_render_loop(render_engine.clone(), waterfall.clone());

    Ok(WaterfallJsAPI {
        waterfall: waterfall,
        render_engine: render_engine,
        shape: shape,
    })
}

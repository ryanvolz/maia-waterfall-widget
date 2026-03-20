import "./widget.css";
import init, { make_waterfall } from "../bindings/pkg/maia_waterfall_widget_wasm";

async function initialize({ model }) {
  await init();
}

function render({ model, el }) {
  el.classList.add("maia_waterfall_widget");
  const canvas = document.createElement("canvas");
  canvas.id = "waterfall";
  canvas.width = model.get("_num_freq_samples");
  canvas.height = model.get("_num_time_samples");
  canvas.style.width = "100%";
  // add canvas to document body so make_waterfall can find it (it can't be
  // found in the document from el because `render` would need to finish first)
  document.body.appendChild(canvas);
  const waterfall = make_waterfall(
    canvas.id,
    model.get("_num_freq_samples"),
    model.get("_num_time_samples"),
  );
  // set initial waterfall state from model
  waterfall.colormap = model.get("colormap");
  waterfall.set_freq_samprate(model.get("center_freq_hz"), model.get("sample_rate_hz"));
  waterfall.spectrum_visible = model.get("spectrum_visible");
  waterfall.waterfall_max_db = model.get("waterfall_max_db");
  waterfall.waterfall_min_db = model.get("waterfall_min_db");
  waterfall.waterfall_update_rate_hz = model.get("waterfall_update_rate_hz");
  waterfall.waterfall_visible = model.get("waterfall_visible");
  // move the waterfall canvas to el
  el.appendChild(canvas);

  model.on("change:center_freq_hz", () => {
    waterfall.center_freq_hz = model.get("center_freq_hz");
  });
  model.on("change:colormap", () => {
    waterfall.colormap = model.get("colormap");
  });
  model.on("change:sample_rate_hz", () => {
    waterfall.sample_rate_hz = model.get("sample_rate_hz");
  });
  model.on("change:spectrum_visible", () => {
    waterfall.spectrum_visible = model.get("spectrum_visible");
  });
  model.on("change:waterfall_max_db", () => {
    waterfall.waterfall_max_db = model.get("waterfall_max_db");
  });
  model.on("change:waterfall_min_db", () => {
    waterfall.waterfall_min_db = model.get("waterfall_min_db");
  });
  model.on("change:waterfall_update_rate_hz", () => {
    waterfall.waterfall_update_rate_hz = model.get("waterfall_update_rate_hz");
  });
  model.on("change:waterfall_visible", () => {
    waterfall.waterfall_visible = model.get("waterfall_visible");
  });
  model.on("msg:custom", (msg, buffers) => {
    if (msg === "put_spectrum") {
      for (const dataview of buffers) {
        let spec = new Float32Array(dataview.buffer);
        waterfall.put_waterfall_spectrum(spec);
      }
    }
  });
}

export default { initialize, render };

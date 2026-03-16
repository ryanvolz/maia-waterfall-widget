import "./widget.css";
import init, { make_waterfall } from "../bindings/pkg/maia_waterfall_widget_wasm";

async function initialize({ model }) {
  await init();
}

function render({ model, el }) {
  el.classList.add("maia_waterfall_widget");
  const canvas = document.createElement("canvas");
  canvas.id = "waterfall";
  canvas.style.width = "100%";
  // add canvas to document body so make_waterfall can find it (it can't be
  // found in the document from el because `render` would need to finish first)
  document.body.appendChild(canvas);
  const waterfall = make_waterfall(canvas.id);
  console.log(waterfall);
  // set initial waterfall state from model
  waterfall.spectrum_visible = model.get("spectrum_visible");
  // move the waterfall canvas to el
  el.appendChild(canvas);

  model.on("change:spectrum_visible", () => {
    waterfall.spectrum_visible = model.get("spectrum_visible");
  });
  console.log("render() done");
}

export default { initialize, render };

import "./widget.css";
import init, { make_waterfall } from "../bindings/pkg/maia_waterfall_widget";

async function initialize({ model }) {
  await init();
}

function render({ model, el }) {
  el.classList.add("maia_waterfall_widget");
  let canvas = document.createElement("canvas");
  canvas.id = "waterfall";
  el.appendChild(canvas);
  // defer make_waterfall until the canvas has rendered
  setTimeout(() => {
    waterfall = make_waterfall("waterfall");
    // why is waterfall undefined?
    console.log(waterfall);
    // waterfall.set_spectrum_visible(model.get("spectrum_visible"));
  }, 10);

  model.on("change:spectrum_visible", () => {});
  console.log("render() done");
}

export default { initialize, render };

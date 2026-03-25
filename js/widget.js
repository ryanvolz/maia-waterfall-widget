import mqtt from "mqtt";

import "./widget.css";
import init, { make_waterfall } from "../bindings/pkg/maia_waterfall_widget_wasm";

async function initialize({ model }) {
  await init();
}

function render({ model, el }) {
  // put canvas in a div so we have different ways to style it, like flex
  const div = document.createElement("div");
  div.classList.add("maia_waterfall_widget");
  // add div to document body so make_waterfall can find it its canvas (it can't be
  // found in the document from el because `render` would need to finish first)
  document.body.appendChild(div);
  const canvas = document.createElement("canvas");
  canvas.classList.add("maia_waterfall_widget");
  canvas.id = "waterfall-" + window.crypto.randomUUID();
  canvas.width = model.get("_num_freq_samples");
  canvas.height = model.get("_num_time_samples");
  // add canvas to document body so make_waterfall can find it (it can't be
  // found in the document from el because `render` would need to finish first)
  div.appendChild(canvas);
  const waterfall = make_waterfall(
    canvas.id,
    model.get("_num_freq_samples"),
    model.get("_num_time_samples"),
  );
  // move the waterfall div to el
  el.appendChild(div);

  const resizeObserver = new ResizeObserver(() => {
    waterfall.resize_canvas();
  });
  resizeObserver.observe(canvas);

  // set initial waterfall state from model
  waterfall.colormap = model.get("colormap");
  waterfall.set_freq_samprate(model.get("center_freq_hz"), model.get("sample_rate_hz"));
  waterfall.spectrum_visible = model.get("spectrum_visible");
  waterfall.waterfall_max_db = model.get("waterfall_max_db");
  waterfall.waterfall_min_db = model.get("waterfall_min_db");
  waterfall.waterfall_update_rate_hz = model.get("waterfall_update_rate_hz");
  waterfall.waterfall_visible = model.get("waterfall_visible");

  // initialize mqtt
  const mqtt_state = {
    client: null,
    topic: model.get("mqtt_topic"),
  };
  if (model.get("mqtt_url")) {
    // connect and, if there's a topic, subscribe
    connect_mqtt({ model: model, mqtt_state: mqtt_state, waterfall: waterfall });
  }

  model.on("change:center_freq_hz", () => {
    waterfall.center_freq_hz = model.get("center_freq_hz");
  });
  model.on("change:colormap", () => {
    waterfall.colormap = model.get("colormap");
  });
  model.on("change:mqtt_topic", () => {
    subscribe_mqtt({ model: model, mqtt_state: mqtt_state });
  });
  model.on("change:mqtt_url", () => {
    connect_mqtt({ model: model, mqtt_state: mqtt_state, waterfall: waterfall });
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

function connect_mqtt({ model, mqtt_state, waterfall }) {
  if (mqtt_state.client) {
    // disconnect existing client
    mqtt_state.client.end(true);
    mqtt_state.client = null;
  }
  if (model.get("mqtt_url")) {
    const options = {
      // MQTT version 5 needed for spectrum metadata sent as properties
      protocolVersion: 5,
    };
    mqtt_state.client = mqtt.connect(model.get("mqtt_url"), options);
    mqtt_state.client.on("connect", (connack) => {
      console.log(`Connected to ${model.get("mqtt_url")}`);
    });
    mqtt_state.client.on("close", () => {
      console.log(`Disonnected from ${model.get("mqtt_url")}`);
    });
    mqtt_state.client.on("error", (error) => {
      console.log("MQTT error:");
      console.log(error);
    });
    mqtt_state.client.on("message", (topic, payload, packet) => {
      if (packet.properties.contentType == "<float32") {
        const shape = JSON.parse(packet.properties.userProperties.shape);
        if (shape[1] != model.get("_num_freq_samples")) {
          console.info(`Received spectrum shape ${shape} does not match in number of \
frequency bins ${model.get("_num_freq_samples")}. Discarding.`);
          return;
        }
        const sample_rate_hz = JSON.parse(
          packet.properties.userProperties.sample_rate_hz,
        );
        const center_freq_hz = JSON.parse(
          packet.properties.userProperties.center_freq_hz,
        );
        if (
          sample_rate_hz != model.get("sample_rate_hz") ||
          center_freq_hz != model.get("center_freq_hz")
        ) {
          model.set("sample_rate_hz", sample_rate_hz);
          model.set("center_freq_hz", center_freq_hz);
        }
        const spectrum_rate_hz = JSON.parse(
          packet.properties.userProperties.spectrum_rate_hz,
        );
        if (spectrum_rate_hz != model.get("waterfall_update_rate_hz")) {
          model.set("waterfall_update_rate_hz", spectrum_rate_hz);
        }
        const full_spec = new Float32Array(
          // slice buffer to force copy since it might not be aligned for float32
          payload.buffer.slice(payload.byteOffset, payload.byteOffset + payload.length),
        );
        const subch = 0;
        const spec = full_spec.subarray(subch * shape[1], (subch + 1) * shape[1]);
        waterfall.put_waterfall_spectrum(spec);
      }
      // radiohound format
      //   const msg = JSON.parse(payload);
      //   if (msg.data && msg.type == "float32") {
      //     const bytes = Uint8Array.fromBase64(msg.data);
      //     let spec = new Float32Array(bytes.buffer);
      //     waterfall.put_waterfall_spectrum(spec);
      //     if (
      //       msg.sample_rate != model.get("sample_rate_hz") ||
      //       msg.center_frequency != model.get("center_freq_hz")
      //     ) {
      //       waterfall.set_freq_samprate(msg.center_frequency, msg.sample_rate);
      //     }
      //   }
    });
    if (mqtt_state.topic) {
      // re-subscribe to existing topic
      mqtt_state.client.subscribe(mqtt_state.topic);
    }
  }
}

function subscribe_mqtt({ model, mqtt_state }) {
  if (mqtt_state.client) {
    // unsubscribe from prior topic
    if (mqtt_state.topic) {
      mqtt_state.client.unsubscribe(mqtt_state.topic);
      mqtt_state.topic = "";
    }
    if (model.get("mqtt_topic")) {
      mqtt_state.client.subscribe(model.get("mqtt_topic"));
    }
  }
  mqtt_state.topic = model.get("mqtt_topic");
}

export default { initialize, render };

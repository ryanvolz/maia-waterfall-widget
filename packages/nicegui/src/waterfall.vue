<script setup>
import { computed, onMounted, ref, useId, watchEffect } from "vue";
import { vResizeObserver } from "@vueuse/components";
import { make_waterfall } from "maia-waterfall";

const props = defineProps({
    // Normal props that are only set by the parent
    numFreqSamples: { type: Number, required: true },
    numTimeSamples: { type: Number, required: true },
    rangeMaxDb: { type: Number, default: 10 },
    rangeMinDb: { type: Number, default: -150 },
    toolbarMaxHeight: { type: Number, default: 40 },

    // Props for "model" values (there is an accompanying emit when changed)
    // We use these and define the emits manually instead of using defineModel()
    // because most of these are already defined as local state in the
    // `waterfall` object and this way we don't have to have duplicate local
    // state variables to manage and keep in sync.
    averagingCount: { type: Number, default: 1 },
    colormap: { type: String, default: "turbo" },
    maxDb: { type: Number, default: 3 },
    minDb: { type: Number, default: -40 },
    spectrumVisible: Boolean,
    toolbarHeight: { type: Number, default: 40 },
    waterfallVisible: Boolean,
});

const waterfallCanvasId = useId();
const waterfall = ref({});

// For updating values that are stored locally and can be changed
// locally in the client from the corresponding props
const update_from_props = () => {
    waterfall.value.averaging_count = props.averagingCount;
    waterfall.value.colormap = props.colormap;
    waterfall.value.spectrum_visible = props.spectrumVisible;
    waterfall.value.waterfall_max_db = props.maxDb;
    waterfall.value.waterfall_min_db = props.minDb;
    waterfall.value.waterfall_visible = props.waterfallVisible;
}
// Set initial local values from props and react to updates
watchEffect(update_from_props);

const emit = defineEmits([
    "update:averaging-count",
    "update:colormap",
    "update:max-db",
    "update:min-db",
    "update:num-freq-samples",
    "update:num-time-samples",
    "update:spectrum-visible",
    "update:toolbar-height",
    "update:waterfall-visible"
]);

const averagingCountNonlinear = computed({
    get() {
        return Math.pow(waterfall.value.averaging_count, 1 / 3)
    },
    set(newVal) {
        waterfall.value.averaging_count = Math.round(Math.pow(newVal, 3));
    }
})

const colormapOptions = [
    { label: "Turbo", value: "turbo" },
    { label: "Viridis", value: "viridis" },
    { label: "Inferno", value: "inferno" },
]

const updateRangeDb = (event) => {
    if (waterfall.waterfall_max_db !== event.max) {
        emit("update:max-db", event.max);
        waterfall.waterfall_max_db = event.max;
    }
    if (waterfall.waterfall_min_db !== event.min) {
        emit("update:min-db", event.min);
        waterfall.waterfall_min_db = event.min;
    }
}

onMounted(() => {
    waterfall.value = make_waterfall(
        waterfallCanvasId,
        props.numFreqSamples,
        props.numTimeSamples,
    );
    update_from_props();
});

const set_freq_samprate = (args) => {
    waterfall.value.set_freq_samprate(args.center_freq_hz, args.sample_rate_hz);
}

const set_spectrum_rate = (args) => {
    waterfall.value.waterfall_update_rate_hz = args.spectrum_rate_hz;
}

const put_spectrum = (args) => {
    const bytes = Uint8Array.fromBase64(args.data);
    const spec = new Float32Array(bytes.buffer);
    waterfall.value.put_waterfall_spectrum(spec);
}

function handle_canvas_resize() {
    waterfall.value.resize_canvas?.();
}

defineExpose({ put_spectrum, set_freq_samprate, set_spectrum_rate, update_from_props, waterfall });
</script>

<template>
    <div class="fit col column no-wrap" style="min-height: inherit; max-height: 0px">
        <q-splitter class="fit col" :model-value="toolbarHeight"
            @update:model-value="$emit('update:toolbar-height', $event)" horizontal reverse unit="px"
            :limits="[0, toolbarMaxHeight]" before-class="column no-wrap">
            <template #before>
                <!-- Waterfall engine only handles resize when window resizes, so to handle canvas-only resizes we need the resize observer -->
                <canvas class="fit col" :id="waterfallCanvasId" v-resize-observer:1000="handle_canvas_resize" />
            </template>

            <template #after>
                <div class="fit row q-gutter-x-xs justify-center items-start">
                    <slot name="before"></slot>
                    <q-checkbox class="col-auto q-pr-xs" v-model="waterfall.waterfall_visible"
                        @update:model-value="$emit('update:waterfall-visible', $event)" label="Waterfall">
                        <q-tooltip cursor-position delay="1000" anchor="center" self="bottom">Toggle waterfall
                            visibility</q-tooltip>
                    </q-checkbox>
                    <q-checkbox class="col-auto q-pr-xs" v-model="waterfall.spectrum_visible"
                        @update:model-value="$emit('update:spectrum-visible', $event)" label="Spectrum">
                        <q-tooltip cursor-position delay="1000" anchor="center" self="bottom">Toggle spectrum
                            visibility</q-tooltip>
                    </q-checkbox>
                    <q-select class="col-auto q-ml-sm" style="min-width: 7em" v-model="waterfall.colormap"
                        @update:model-value="$emit('update:colormap', $event)" :options="colormapOptions"
                        label="Colormap" emit-value map-options stack-label dense options-dense borderless />
                    <q-field class="col q-mx-xs" style="min-width: 18em; max-width: 40em" label="Colormap limits [dB]"
                        stack-label borderless dense>
                        <template #before>
                            <q-input class="col-auto q-ml-sm" v-model.number.lazy="waterfall.waterfall_min_db"
                                @update:model-value="$emit('update:min-db', $event)" type="number" label="Min"
                                :min="rangeMinDb" :max="waterfall.waterfall_max_db" stack-label dense borderless />
                        </template>
                        <template #control>
                            <q-range class="q-mt-sm"
                                :model-value="{ min: waterfall.waterfall_min_db, max: waterfall.waterfall_max_db }"
                                @update:model-value="updateRangeDb" :min="rangeMinDb" :max="rangeMaxDb" :step="1" snap
                                :markers="10" drag-range dense />
                        </template>
                        <template #after>
                            <q-input class="col-auto q-mr-sm" v-model.number.lazy="waterfall.waterfall_max_db"
                                @update:model-value="$emit('update:max-db', $event)" type="number" label="Max"
                                :min="waterfall.waterfall_min_db" :max="rangeMaxDb" stack-label dense borderless />
                        </template>
                    </q-field>
                    <q-field class="col q-mx-xs" style="min-width: 12em; max-width: 24em" label="Averaging count"
                        stack-label borderless dense>
                        <template #control>
                            <q-slider class="q-mt-sm" v-model.number.lazy="averagingCountNonlinear"
                                @update:model-value="$emit('update:averaging-count', Math.round(Math.pow($event, 3)))"
                                :min="1" :max="Math.pow(10000, 1 / 3)"
                                :step="Math.pow(10000, 1 / 3) - Math.pow(10000 - 1, 1 / 3)"
                                :label-value="waterfall.averaging_count" dense />
                        </template>
                        <template #after>
                            <q-input class="col-auto q-mr-sm" v-model.number.lazy="waterfall.averaging_count"
                                @update:model-value="$emit('update:averaging-count', $event)" type="number"
                                label="# spectra" :min="1" :max="10000" stack-label dense borderless />
                        </template>
                    </q-field>
                    <!--<q-input ref="numTimeInput" class="col-auto q-mr-sm" :model-value="state.numTimeSamples"
                        @change="setNumTimeSamples" type="number" label="# time" :min="1" :max="10000" required
                        stack-label dense borderless />-->
                    <slot></slot>
                    <slot name="after"></slot>
                </div>
            </template>
        </q-splitter>
    </div>
</template>

<style scoped>
canvas {
    user-select: none;
    -webkit-user-select: none;
    -ms-user-select: none;
}
</style>

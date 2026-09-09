<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from "vue";
import { init, use, type EChartsCoreOption, type EChartsType } from "echarts/core";
import { BarChart, PieChart, TreemapChart, ScatterChart, HeatmapChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent, CalendarComponent, VisualMapComponent, GraphicComponent, AriaComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

use([BarChart, PieChart, TreemapChart, ScatterChart, HeatmapChart, GridComponent, LegendComponent, TooltipComponent, CalendarComponent, VisualMapComponent, GraphicComponent, AriaComponent, CanvasRenderer]);
export type ChartSelection = { name: string; data: unknown; value: unknown; seriesName?: string };
const props = defineProps<{ option: EChartsCoreOption; label: string; empty?: boolean }>();
const emit = defineEmits<{ select: [selection: ChartSelection] }>();
const root = ref<HTMLElement>();
let chart: EChartsType | undefined;
let observer: ResizeObserver | undefined;
onMounted(() => {
  if (!root.value) return;
  chart = init(root.value, undefined, { renderer: "canvas", devicePixelRatio: Math.min(window.devicePixelRatio, 2) });
  chart.setOption(props.option);
  chart.on("click", (event) => emit("select", { name: String(event.name ?? ""), data: event.data, value: event.value, seriesName: event.seriesName }));
  observer = new ResizeObserver(() => chart?.resize());
  observer.observe(root.value);
});
watch(() => props.option, (option) => {
  chart?.setOption(option, { notMerge: true });
  if (props.empty) root.value?.setAttribute("aria-label", `${props.label}，暂无文章`);
});
onBeforeUnmount(() => { observer?.disconnect(); chart?.dispose(); });
</script>

<template>
  <div class="dashboard-chart-wrap">
    <div ref="root" class="dashboard-chart" role="img" :aria-label="label"></div>
    <span v-if="empty" class="dashboard-chart-empty">暂无文章</span>
  </div>
</template>

<style scoped>
.dashboard-chart-wrap { width: 100%; height: 100%; min-height: 0; position: relative; }
.dashboard-chart { width: 100%; height: 100%; }
.dashboard-chart-empty { position: absolute; inset: 0; display: grid; place-items: center; color: #56747c; background: rgba(235,244,239,.7); font-size: 14px; pointer-events: none; }
</style>

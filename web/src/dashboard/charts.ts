import type { EChartsCoreOption } from "echarts/core";
import { chartColors, type DashboardSummary } from "./data";

const ink = "#315563";
const line = "rgba(66,119,128,.17)";
const font = '"Noto Sans SC", "Microsoft YaHei", sans-serif';
const axis = { axisLine: { lineStyle: { color: line } }, axisTick: { show: false }, axisLabel: { color: ink, fontSize: 12 }, splitLine: { lineStyle: { color: line, type: "dashed" as const } }, nameTextStyle: { color: ink } };
const base = { animationDuration: 450, color: chartColors, textStyle: { fontFamily: font, color: ink }, tooltip: { trigger: "item", renderMode: "richText", confine: true, backgroundColor: "#f4f9f6", borderColor: "#b6d4d3", textStyle: { color: "#254a4b", fontFamily: font } }, aria: { enabled: true } };

export function dashboardChartOptions(summary: DashboardSummary, year: number, reducedMotion: boolean): Record<string, EChartsCoreOption> {
  const shared = { ...base, animation: !reducedMotion };
  const categoryColor = (category: string) => chartColors[Math.max(0, summary.categories.findIndex((item) => item.name === category)) % chartColors.length];
  const calendarValues: [string, number][] = [];
  const dateCounts = new Map(summary.dates.map((item) => [item.name, item.value]));
  const end = new Date(`${summary.cutoff}T00:00:00Z`);
  for (const date = new Date(`${year}-01-01T00:00:00Z`); date <= end && date.getUTCFullYear() === year; date.setUTCDate(date.getUTCDate() + 1)) {
    const key = date.toISOString().slice(0, 10);
    calendarValues.push([key, dateCounts.get(key) ?? 0]);
  }
  return {
    monthly: {
      ...shared, grid: { left: 34, right: 14, top: 24, bottom: 36 },
      xAxis: { ...axis, type: "category", data: summary.months.map((item) => item.name), axisLabel: { ...axis.axisLabel, interval: 0 } },
      yAxis: { ...axis, type: "value", name: "篇", minInterval: 1, splitNumber: 3, interval: Math.max(12, ...summary.months.map((item) => item.value)) <= 12 ? 4 : undefined, max: Math.max(12, ...summary.months.map((item) => item.value)) },
      series: [{ type: "bar", name: "发布文章", barMaxWidth: 30, label: { show: true, position: "top", color: ink, fontSize: 13 }, data: summary.months.map((item, index) => ({ value: item.value, itemStyle: { color: year === Number(summary.cutoff.slice(0, 4)) && index === Number(summary.cutoff.slice(5, 7)) - 1 ? chartColors[1] : chartColors[0] } })) }],
    },
    categories: {
      ...shared, legend: { orient: "vertical", right: 20, top: "middle", icon: "circle", itemWidth: 16, itemHeight: 16, itemGap: 20, textStyle: { color: ink, fontSize: 14, fontFamily: font }, formatter: (name: string) => `${name}    ${summary.categories.find((item) => item.name === name)?.value ?? 0}`, selectedMode: false },
      series: [{ type: "pie", name: "文章分类", radius: ["44%", "88%"], center: ["29%", "45%"], label: { show: true, position: "center", formatter: (params: { dataIndex: number }) => params.dataIndex === 0 ? `{total|${summary.items.length}}\n{caption|篇文章}` : "", rich: { total: { color: "#133d4c", fontSize: 31, fontWeight: 700, fontFamily: font, lineHeight: 36 }, caption: { color: ink, fontSize: 14, fontFamily: font, lineHeight: 20 } } }, labelLine: { show: false }, itemStyle: { borderColor: "#edf5ee", borderWidth: 1 }, data: summary.categories, emphasis: { scaleSize: 4 } }],
    },
    series: {
      ...shared, grid: { left: 122, right: 28, top: 8, bottom: 23 },
      xAxis: { ...axis, type: "value", minInterval: 1, splitNumber: 3, interval: Math.max(1, ...summary.series.map((item) => item.value)) === 18 ? 6 : undefined, max: Math.max(1, ...summary.series.map((item) => item.value)), name: "篇", splitLine: { show: false } },
      yAxis: { ...axis, type: "category", inverse: true, data: summary.series.slice(0, 4).map((item) => item.name), axisLabel: { ...axis.axisLabel, width: 110, overflow: "truncate" } },
      series: [{ type: "bar", name: "专题文章", barMaxWidth: 15, label: { show: true, position: "right", color: ink }, data: summary.series.slice(0, 4).map((item, index) => ({ name: item.name, value: item.value, itemStyle: { color: ["#358d96", "#62a7ae", "#78b6b8", "#81b6ae"][index] } })) }],
    },
    tags: {
      ...shared,
      series: [{ type: "treemap", name: "技术标签", left: 0, top: 0, right: 0, bottom: 2, roam: false, nodeClick: false, breadcrumb: { show: false }, sort: "desc", squareRatio: 1, colorMappingBy: "index", itemStyle: { borderWidth: 1, gapWidth: 2, borderColor: "#eaf1ed" }, label: { show: true, position: "insideTopLeft", padding: [9, 4], formatter: "{b}\n{c}", fontSize: 12, lineHeight: 24, overflow: "truncate", color: "#ffffff", textShadowColor: "rgba(14,55,63,.25)", textShadowBlur: 2 }, data: summary.tags.slice(0, 8).map((item, index) => ({ ...item, itemStyle: { color: ["#368e97", "#78a48e", "#d1806c", "#c6a952", "#70a29a", "#82ab97", "#368e97", "#c6a952"][index] } })) }],
      media: [
        { query: { maxHeight: 180 }, option: { series: [{ label: { formatter: "{b}  {c}", padding: [4, 3], fontSize: 11, lineHeight: 15 } }] } },
        { option: { series: [{ label: { formatter: "{b}\n{c}", padding: [9, 4], fontSize: 12, lineHeight: 24 } }] } },
      ],
    },
    scatter: {
      ...shared, grid: { left: 39, top: 28, right: 20, bottom: 57 },
      legend: { bottom: 0, itemWidth: 11, itemHeight: 11, itemGap: 12, textStyle: { color: ink, fontSize: 11 } },
      xAxis: { ...axis, type: "value", name: "阅读次数", nameLocation: "middle", nameGap: 26, splitNumber: 4, axisLabel: { color: ink, formatter: (value: number) => value >= 1000 ? `${value / 1000}k` : String(value) } },
      yAxis: { ...axis, type: "value", name: "获赞数", splitNumber: 3 },
      series: summary.categories.map((category) => ({ type: "scatter", name: category.name, symbolSize: 7, itemStyle: { color: categoryColor(category.name), opacity: 0.9 }, data: summary.items.filter((item) => item.category === category.name).map((item) => ({ name: item.title, value: [item.views, item.likes], articleId: item.id })) })),
    },
    lengths: {
      ...shared, grid: { left: 90, right: 38, top: 5, bottom: 8 },
      xAxis: { type: "value", show: false },
      yAxis: { ...axis, type: "category", inverse: true, data: summary.lengths.map((item) => item.name) },
      series: [{ type: "bar", name: "文章篇数", barMaxWidth: 18, showBackground: true, backgroundStyle: { color: "rgba(82,145,148,.13)" }, label: { show: true, position: "right", distance: 10, color: ink }, labelLayout: (params: { rect: { x: number; width: number }; dataIndex: number }) => ({ x: params.rect.x + params.rect.width * Math.max(1, ...summary.lengths.map((item) => item.value)) / Math.max(1, summary.lengths[params.dataIndex]?.value ?? 1) + 10 }), data: summary.lengths }],
    },
    calendar: {
      ...shared,
      visualMap: { show: false, min: 0, max: Math.max(3, ...summary.dates.map((item) => item.value)), inRange: { color: ["#d9e9e8", "#b6d6d3", "#8ebfbc", "#5e9fa2", "#297c86"] } },
      calendar: { range: String(year), left: 37, right: 3, top: 25, bottom: 23, cellSize: ["auto", "auto"], splitLine: { show: false }, yearLabel: { show: false }, dayLabel: { firstDay: 1, nameMap: ["周日", "周一", "周二", "周三", "周四", "周五", "周六"], color: "#607f87", margin: 6, fontSize: 9 }, monthLabel: { nameMap: Array.from({ length: 12 }, (_, i) => `${i + 1}月`), color: ink, fontSize: 10, margin: 7 }, itemStyle: { color: "rgba(233,243,240,.6)", borderColor: "#bfd8d6", borderWidth: .5 } },
      series: [{ type: "heatmap", coordinateSystem: "calendar", name: "发布文章", itemStyle: { borderWidth: 2, borderColor: "#e7f0ec" }, data: calendarValues }],
    },
  };
}

export type DashboardArticle = {
  id: number;
  slug: string;
  title: string;
  category: string;
  tags: string[];
  series: string | null;
  published: string;
  updated: string;
  words: number;
  views: number;
  likes: number;
};

export type CountItem = { name: string; value: number };
export const categoryNames = ["前端开发", "后端实践", "工程实践", "生活随笔"];
export const chartColors = ["#388c95", "#d47f6b", "#7da38d", "#c9ae58", "#629d9b", "#af9280"];
export const sampleCutoff = "2026-09-08";
export const lengthNames = ["1千字以下", "1千—3千字", "3千—5千字", "5千字及以上"];

export function lengthIndex(words: number) {
  return words < 1000 ? 0 : words < 3000 ? 1 : words < 5000 ? 2 : 3;
}

function counts(names: string[]): CountItem[] {
  const map = new Map<string, number>();
  for (const name of names) map.set(name, (map.get(name) ?? 0) + 1);
  return [...map].map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
}

export function summarizeArticles(articles: DashboardArticle[], year: number, today: string, seriesNames: string[] = []) {
  const cutoff = year < Number(today.slice(0, 4)) ? `${year}-12-31` : today;
  const items = articles.filter((item) => item.published <= cutoff && Number(item.published.slice(0, 4)) <= year);
  const annual = items.filter((item) => Number(item.published.slice(0, 4)) === year);
  const months = Array.from({ length: year < Number(today.slice(0, 4)) ? 12 : Number(today.slice(5, 7)) }, (_, index) => ({ name: `${index + 1}月`, value: annual.filter((item) => Number(item.published.slice(5, 7)) === index + 1).length }));
  const dates = counts(annual.map((item) => item.published)).sort((a, b) => a.name.localeCompare(b.name));
  const categories = counts(items.map((item) => item.category));
  const series = counts(items.flatMap((item) => item.series ? [item.series] : []));
  const totalViews = items.reduce((sum, item) => sum + item.views, 0);
  const totalLikes = items.reduce((sum, item) => sum + item.likes, 0);
  return {
    items, annual, cutoff, months, dates, categories, series,
    tags: counts(items.flatMap((item) => [...new Set(item.tags)])),
    seriesCount: new Set([...seriesNames, ...series.map((item) => item.name)]).size,
    seriesArticleCount: items.filter((item) => item.series).length,
    words: items.reduce((sum, item) => sum + item.words, 0),
    totalViews, totalLikes,
    averageViews: items.length ? Math.round(totalViews / items.length) : 0,
    averageLikes: items.length ? (totalLikes / items.length).toFixed(1) : "0",
    lengths: lengthNames.map((name, index) => ({ name, value: items.filter((item) => lengthIndex(item.words) === index).length })),
    recent: [...items].sort((a, b) => b.updated.localeCompare(a.updated)).slice(0, 3),
  };
}

export type DashboardSummary = ReturnType<typeof summarizeArticles>;

export function createSampleArticles(): DashboardArticle[] {
  const monthTotals = [8, 10, 7, 12, 9, 11, 8, 11, 4];
  const dates: string[] = [];
  // 演示文章同样从明细聚合，保证年历、各分组和总数一致。
  for (let year = 2024; year <= 2025; year++) {
    for (let month = 1; month <= 12; month++) {
      for (const day of [8, 20]) dates.push(`${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`);
    }
  }
  monthTotals.forEach((amount, index) => {
    const activeDays = index === 8 ? [6, 8] : [2 + index % 3, 7 + index * 2 % 4, 14 + index * 3 % 4, 21 + index * 2 % 3, 27];
    for (let i = 0; i < amount; i++) dates.push(`2026-${String(index + 1).padStart(2, "0")}-${String(activeDays[i % activeDays.length]).padStart(2, "0")}`);
  });
  dates.sort((a, b) => b.localeCompare(a));
  const titles = ["Vue 3 组件设计笔记", "从零搭建个人博客", "FastAPI 接口实践", "Three.js 海上展馆", "写给持续创作的自己"];
  const topicNames = ["Vue 深入实践", "全栈博客实录", "三维交互探索", "后端工程笔记", "组件与设计", "性能与优化", "工程自动化", "数据库手记", "前端基础", "日常记录", "阅读笔记", "开发工具"];
  const topicSizes = [18, 12, 8, 7, 7, 7, 7, 6, 6, 6, 6, 6];
  const topics = topicNames.flatMap((name, index) => Array.from({ length: topicSizes[index] }, () => name));
  const categories = categoryNames.flatMap((name, index) => Array.from({ length: [56, 32, 24, 16][index] }, () => name));
  const tags = ["Vue", "TypeScript", "FastAPI", "工程化", "Three.js", "Python", "CSS", "MySQL"];
  const tagTotals = [35, 28, 24, 21, 18, 15, 12, 10];
  const result = dates.map((date, i) => ({
    id: i + 1, slug: `sample-${i + 1}`,
    title: titles[i] ?? `${categories[i * 37 % 128]} · ${["实践笔记", "问题复盘", "阅读记录", "探索与总结"][i % 4]} ${String(i + 1).padStart(2, "0")}`,
    category: categories[i * 37 % 128]!, tags: tags.filter((_, index) => (i * 37 + index * 11) % 128 < tagTotals[index]!),
    series: topics[i] ?? null, published: date, updated: date,
    words: i < 24 ? 450 : i < 82 ? 1950 : i < 112 ? 3800 : i === 127 ? 5510 : 5506,
    views: i < 5 ? [3842, 3216, 2865, 2408, 1976][i]! : 0,
    likes: i < 5 ? [286, 242, 187, 168, 133][i]! : 0,
  }));
  const remainingViews = 38592 - result.reduce((sum, item) => sum + item.views, 0);
  const remainingLikes = 2316 - result.reduce((sum, item) => sum + item.likes, 0);
  const allocate = (total: number, weights: number[]) => {
    const sum = weights.reduce((a, b) => a + b, 0);
    const values = weights.map((weight) => Math.floor(total * weight / sum));
    const remainder = total - values.reduce((a, b) => a + b, 0);
    return values.map((value, i) => value + (i < remainder ? 1 : 0));
  };
  const weights = Array.from({ length: 123 }, (_, i) => ((123 - i) / 123) ** 6 * (0.5 + (i * 17 % 31) / 31) + 0.004);
  const views = allocate(remainingViews, weights);
  const likes = allocate(remainingLikes, weights.map((weight, i) => weight ** .85 * (.3 + (i * 13 % 19) / 19)));
  for (let i = 5; i < result.length; i++) { result[i]!.views = views[i - 5]!; result[i]!.likes = likes[i - 5]!; }
  result[1]!.published = "2026-09-06"; result[1]!.updated = "2026-09-06";
  result[2]!.updated = "2026-09-06T14:32";
  result[3]!.updated = "2026-09-07";
  return result;
}

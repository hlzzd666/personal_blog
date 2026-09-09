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
export const chartColors = ["#388c95", "#d47f6b", "#7da38d", "#c9ae58", "#629d9b", "#af9280"];
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

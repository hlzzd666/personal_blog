import { marked } from "marked";
import DOMPurify from "dompurify";
import { fetchArticles } from "./articles";
import { fetchSeries } from "./content";
import type { DashboardArticle } from "../dashboard/data";
import { request } from "./http";

export type DailyVisitorStats = {
  days: Array<{ date: string; visits: number }>;
  today_visits: number;
};

export function articleWordCount(markdown: string) {
  const document = new DOMParser().parseFromString(DOMPurify.sanitize(marked.parse(markdown, { async: false })), "text/html");
  document.querySelectorAll("pre, code, img, script, style").forEach((element) => element.remove());
  return (document.body.textContent?.match(/[\p{Script=Han}]|[\p{L}\p{N}]+/gu) ?? []).length;
}

export async function fetchDashboardArticles() {
  const [first, seriesResponse] = await Promise.all([fetchArticles({ page: 1, page_size: 50 }), fetchSeries()]);
  if (first.total > 10000) throw new Error("文章数量超过大屏汇总范围，请联系站长配置服务端统计。");
  const articles = [...first.items];
  const pageCount = Math.ceil(first.total / 50);
  for (let start = 2; start <= pageCount; start += 4) {
    const pages = await Promise.all(Array.from({ length: Math.min(4, pageCount - start + 1) }, (_, index) => fetchArticles({ page: start + index, page_size: 50 })));
    articles.push(...pages.flatMap((page) => page.items));
  }
  const unique = [...new Map(articles.map((article) => [article.id, article])).values()];
  if (unique.length !== first.total) throw new Error("文章列表刚刚发生变化，请刷新后重试。");
  const series = new Map(seriesResponse.items.map((item) => [item.id, item.title]));
  const items: DashboardArticle[] = unique.map((article) => ({
    id: article.id, slug: article.slug, title: article.title,
    category: article.category || "未分类", tags: article.tags,
    series: article.series_id ? series.get(article.series_id) ?? null : null,
    published: (article.published_at || article.created_at).slice(0, 10),
    updated: article.updated_at.slice(0, 10), words: articleWordCount(article.content_markdown),
    views: Math.max(0, article.views), likes: Math.max(0, article.likes),
  }));
  return { items, seriesNames: [...series.values()] };
}

export function fetchDailyVisitorStats() {
  return request<DailyVisitorStats>({ url: "/visitor-records/daily-stats", method: "GET" });
}

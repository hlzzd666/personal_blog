export type ArticleReturnSource = "articles" | "series";

export type ArticleReturnContext = {
  source: ArticleReturnSource;
  path: string;
  scrollY: number;
  articleSlug: string;
  savedAt: number;
};

const articleReturnContextStorageKey = "article-detail-return-context";

function getSessionStorage() {
  return typeof window === "undefined" ? null : window.sessionStorage;
}

export function saveArticleReturnContext(context: Omit<ArticleReturnContext, "savedAt">) {
  getSessionStorage()?.setItem(
    articleReturnContextStorageKey,
    JSON.stringify({ ...context, savedAt: Date.now() }),
  );
}

export function readArticleReturnContext(): ArticleReturnContext | null {
  const storedContext = getSessionStorage()?.getItem(articleReturnContextStorageKey);
  if (!storedContext) return null;

  try {
    const context = JSON.parse(storedContext) as Partial<ArticleReturnContext>;
    if (
      (context.source === "articles" || context.source === "series") &&
      typeof context.path === "string" &&
      typeof context.scrollY === "number" &&
      typeof context.articleSlug === "string" &&
      typeof context.savedAt === "number"
    ) {
      return context as ArticleReturnContext;
    }
  } catch {
    getSessionStorage()?.removeItem(articleReturnContextStorageKey);
  }

  return null;
}


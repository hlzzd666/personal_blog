import { onBeforeUnmount } from "vue";

type SeoOptions = {
  title: string;
  description: string;
  canonicalPath: string;
  image?: string | null;
  type?: "website" | "article";
  jsonLd?: Record<string, unknown>;
};

function upsertMeta(selector: string, attribute: string, value: string) {
  let element = document.head.querySelector<HTMLMetaElement>(selector);
  if (!element) {
    element = document.createElement("meta");
    const [name, content] = attribute.split("=");
    element.setAttribute(name, content);
    document.head.appendChild(element);
  }
  element.dataset.pageSeo = "true";
  element.content = value;
}

export function useSeo() {
  const managedElements: Element[] = [];

  function applySeo(options: SeoOptions) {
    document.title = `${options.title} | 个人博客`;
    upsertMeta('meta[name="description"]', "name=description", options.description);
    upsertMeta('meta[property="og:title"]', "property=og:title", options.title);
    upsertMeta('meta[property="og:description"]', "property=og:description", options.description);
    upsertMeta('meta[property="og:type"]', "property=og:type", options.type ?? "website");
    if (options.image) upsertMeta('meta[property="og:image"]', "property=og:image", options.image);

    const basePath = import.meta.env.BASE_URL.replace(/^\/+|\/+$/g, "");
    const pagePath = options.canonicalPath.replace(/^\/+/, "");
    const canonicalUrl = new URL(`/${[basePath, pagePath].filter(Boolean).join("/")}`, window.location.origin).href;
    let canonical = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.dataset.pageSeo = "true";
    canonical.href = canonicalUrl;

    document.head.querySelector('#page-json-ld')?.remove();
    if (options.jsonLd) {
      const script = document.createElement("script");
      script.id = "page-json-ld";
      script.dataset.pageSeo = "true";
      script.type = "application/ld+json";
      script.textContent = JSON.stringify(options.jsonLd);
      document.head.appendChild(script);
      managedElements.push(script);
    }
  }

  onBeforeUnmount(() => {
    managedElements.forEach((element) => element.remove());
    document.head.querySelectorAll('[data-page-seo="true"]').forEach((element) => element.remove());
  });

  return { applySeo };
}

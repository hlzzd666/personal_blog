import { nextTick, onBeforeUnmount } from "vue";

export function useViewportReveal(selector = "[data-reveal]") {
  let observer: IntersectionObserver | undefined;
  let disposed = false;
  let generation = 0;

  async function observe(root?: HTMLElement | null) {
    if (disposed) return;
    const currentGeneration = ++generation;
    observer?.disconnect();
    observer = undefined;
    await nextTick();
    if (disposed || currentGeneration !== generation) return;
    const scope = root ?? document;
    const elements = Array.from(scope.querySelectorAll<HTMLElement>(selector));
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      elements.forEach((element) => element.classList.add("is-revealed"));
      return;
    }
    observer = new IntersectionObserver(
      (entries) => {
        if (disposed || currentGeneration !== generation) return;
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-revealed");
          observer?.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -6%" },
    );
    elements.forEach((element, index) => {
      element.style.setProperty("--reveal-delay", `${Math.min(index, 5) * 42}ms`);
      observer?.observe(element);
    });
  }

  onBeforeUnmount(() => {
    disposed = true;
    observer?.disconnect();
    observer = undefined;
  });
  return { observe };
}
